import os, json, time
import boto3
import httpx
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

# === ENV ===
REGION         = os.getenv("AWS_REGION", "us-east-1")
QUEUE_URL      = os.getenv("SQS_QUEUE_URL")  # Requerido
SQS_ENDPOINT   = os.getenv("SQS_ENDPOINT")   # Solo para LocalStack; vacío en AWS real
BATCH          = int(os.getenv("SQS_BATCH", "10"))            # <= 10
WAIT           = int(os.getenv("SQS_WAIT", "20"))             # Long polling
VISIBILITY     = int(os.getenv("SQS_VISIBILITY", "60"))       # > tiempo de proceso
LB_TARGET_URL  = os.getenv("LB_TARGET_URL", "http://localhost:8080/orders")
HTTP_TIMEOUT   = float(os.getenv("HTTP_TIMEOUT", "30"))

print("[INIT] Starting consumer with config:", flush=True)
print(f"  REGION: {REGION}", flush=True)
print(f"  QUEUE_URL: {QUEUE_URL}", flush=True)
print(f"  SQS_ENDPOINT: {SQS_ENDPOINT or '(none)'}", flush=True)
print(f"  LB_TARGET_URL: {LB_TARGET_URL}", flush=True)
print(f"  BATCH: {BATCH}, WAIT: {WAIT}, VISIBILITY: {VISIBILITY}", flush=True)

if not QUEUE_URL:
    raise SystemExit("Falta SQS_QUEUE_URL")

# Cliente SQS (usa endpoint_url SOLO si se definió)
sqs_kwargs = {"region_name": REGION, "config": Config(retries={"max_attempts": 3, "mode": "standard"})}
if SQS_ENDPOINT:
    sqs_kwargs["endpoint_url"] = SQS_ENDPOINT
sqs = boto3.client("sqs", **sqs_kwargs)

client = httpx.Client(timeout=HTTP_TIMEOUT)

def deliver_to_orders(payload: dict) -> None:
    # Extraer solo la parte "order"
    order_data = payload.get("order", payload)

    headers = {
        "Idempotency-Key": payload.get("event_id", ""),
        "Content-Type": "application/json",
    }

    print(f"[HTTP] POST {LB_TARGET_URL}", flush=True)
    print(f"[HTTP] Headers: {headers}", flush=True)
    print(f"[HTTP] Payload: {json.dumps(order_data)[:200]}...", flush=True)

    r = client.post(LB_TARGET_URL, json=order_data, headers=headers)
    print(f"[HTTP] Response: {r.status_code} {r.reason_phrase}", flush=True)
    if r.status_code >= 400:
        print(f"[HTTP] Error body: {r.text[:500]}", flush=True)
    r.raise_for_status()

def handle_message(m: dict) -> bool:
    print(f"[MSG] Processing message: {m.get('MessageId')}", flush=True)
    print(f"[MSG] Raw message: {m}", flush=True)

    try:
        body_raw = m["Body"]
        print(f"[MSG] Raw body: '{body_raw}' (len={len(body_raw)})", flush=True)
        body = json.loads(body_raw)  # Debe venir con comillas dobles
        print(f"[MSG] Message body: {json.dumps(body)[:200]}...", flush=True)

        body.setdefault("timestamps", {})
        body["timestamps"]["consumer_received"] = time.time()
    except json.JSONDecodeError as e:
        print(f"[MSG] JSON decode error: {e}", flush=True)
        return False

    # Retries básicos
    for attempt in range(2):
        try:
            print(f"[MSG] Attempt {attempt+1}/2", flush=True)
            body["timestamps"]["orders_call_start"] = time.time()
            deliver_to_orders(body)
            body["timestamps"]["db_committed"] = time.time()

            if "bff_received" in body["timestamps"]:
                total = body["timestamps"]["db_committed"] - body["timestamps"]["bff_received"]
                consumer_delay = body["timestamps"]["consumer_received"] - body["timestamps"]["bff_received"]
                orders_proc = body["timestamps"]["db_committed"] - body["timestamps"]["orders_call_start"]
                print(f"[TIMING] Total: {total*1000:.2f}ms | BFF→SQS→Consumer: {consumer_delay*1000:.2f}ms | Orders: {orders_proc*1000:.2f}ms", flush=True)
            return True
        except httpx.HTTPError as e:
            print(f"[MSG] HTTP error attempt {attempt+1}: {e}", flush=True)
            if attempt == 0:
                time.sleep(1.0)
                continue
            return False
        except Exception as e:
            print(f"[MSG] Unexpected error attempt {attempt+1}: {e}", flush=True)
            return False

def main():
    print("[MAIN] Consumer started, entering main loop...", flush=True)
    while True:
        try:
            print(f"[POLL] receive_message(wait={WAIT}s)...", flush=True)
            resp = sqs.receive_message(
                QueueUrl=QUEUE_URL,
                MaxNumberOfMessages=BATCH,
                WaitTimeSeconds=WAIT,
                VisibilityTimeout=VISIBILITY,
                MessageAttributeNames=["All"],
                AttributeNames=["All"],
            )
        except (BotoCoreError, ClientError) as e:
            print(f"[POLL] SQS receive error: {e}", flush=True)
            time.sleep(2.0)
            continue

        msgs = resp.get("Messages", [])
        if not msgs:
            print("[POLL] No messages", flush=True)
            continue

        print(f"[POLL] Received {len(msgs)}", flush=True)
        to_delete = []
        for i, m in enumerate(msgs):
            print(f"[BATCH] {i+1}/{len(msgs)}", flush=True)
            ok = False
            try:
                ok = handle_message(m)
            except Exception as e:
                print(f"[BATCH] handle_message error: {e}", flush=True)

            if ok:
                to_delete.append({"Id": m["MessageId"], "ReceiptHandle": m["ReceiptHandle"]})
            else:
                print(f"[BATCH] Message {i+1} failed; will be retried by SQS", flush=True)

        if to_delete:
            try:
                print(f"[DELETE] Deleting {len(to_delete)}", flush=True)
                sqs.delete_message_batch(QueueUrl=QUEUE_URL, Entries=to_delete)
                print("[DELETE] ✅ Done", flush=True)
            except (BotoCoreError, ClientError) as e:
                print(f"[DELETE] SQS delete error: {e}", flush=True)
        else:
            print("[DELETE] Nothing to delete", flush=True)

if __name__ == "__main__":
    print("[START] Worker starting up...", flush=True)
    main()
