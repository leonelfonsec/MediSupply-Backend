import os, json, time
import boto3
import httpx
from botocore.exceptions import BotoCoreError, ClientError

# === ENV ===
REGION = os.getenv("AWS_REGION", "us-east-1")
QUEUE_URL = os.getenv("SQS_QUEUE_URL")  # p.ej. http://localstack:4566/000000000000/orders.fifo
SQS_ENDPOINT = os.getenv("SQS_ENDPOINT")  # p.ej. http://localstack:4566 (vacío en AWS real)
BATCH = int(os.getenv("SQS_BATCH", "10"))           # <= 10
WAIT = int(os.getenv("SQS_WAIT", "20"))             # long polling
VISIBILITY = int(os.getenv("SQS_VISIBILITY", "60")) # > tiempo de proceso
LB_TARGET_URL = os.getenv("LB_TARGET_URL", "http://localhost:8080/orders")  # URL completa (con path)
HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "30"))

print(f"[INIT] Starting consumer with config:", flush=True)
print(f"  REGION: {REGION}", flush=True)
print(f"  QUEUE_URL: {QUEUE_URL}", flush=True)
print(f"  SQS_ENDPOINT: {SQS_ENDPOINT}", flush=True)
print(f"  LB_TARGET_URL: {LB_TARGET_URL}", flush=True)
print(f"  BATCH: {BATCH}, WAIT: {WAIT}, VISIBILITY: {VISIBILITY}", flush=True)

if not QUEUE_URL:
    raise SystemExit("Falta SQS_QUEUE_URL")

sqs = boto3.client("sqs", region_name=REGION)
client = httpx.Client(timeout=HTTP_TIMEOUT)

def deliver_to_orders(payload: dict) -> None:
    # Extraer solo la parte "order" del payload SQS
    order_data = payload.get("order", payload)
    
    # Agregar el Idempotency-Key header
    headers = {
        "Idempotency-Key": payload.get("event_id", ""),
        "Content-Type": "application/json"
    }
    
    print(f"[HTTP] POST {LB_TARGET_URL}", flush=True)
    print(f"[HTTP] Headers: {headers}", flush=True)
    print(f"[HTTP] Payload: {json.dumps(order_data)[:200]}...", flush=True)
    
    r = client.post(LB_TARGET_URL, json=order_data, headers=headers)
    print(f"[HTTP] Response: {r.status_code} {r.reason_phrase}", flush=True)
    
    if r.status_code >= 400:
        print(f"[HTTP] Error response body: {r.text[:500]}", flush=True)
    
    r.raise_for_status()

def handle_message(m: dict) -> bool:
    print(f"[MSG] Processing message: {m['MessageId']}", flush=True)
    print(f"[MSG] Raw message: {m}", flush=True)  # ← NUEVO: ver todo el mensaje
    
    try:
        body_raw = m["Body"]
        print(f"[MSG] Raw body: '{body_raw}' (length: {len(body_raw)})", flush=True)  # ← NUEVO
        
        body = json.loads(body_raw)
        print(f"[MSG] Message body: {json.dumps(body)[:200]}...", flush=True)

        if "timestamps" not in body:
            body["timestamps"] = {}
        body["timestamps"]["consumer_received"] = time.time()

    except json.JSONDecodeError as e:
        print(f"[MSG] JSON decode error: {e}", flush=True)
        return False
    
    # Retries básicos de red/HTTP
    for attempt in range(2):
        try:
            print(f"[MSG] Attempt {attempt + 1}/2", flush=True)
            
            body["timestamps"]["orders_call_start"] = time.time()
            
            deliver_to_orders(body)
            
            # ✅ USAR ESTO como proxy del DB commit
            body["timestamps"]["db_committed"] = time.time()
            
            # ✅ CALCULAR TIEMPO TOTAL
            if "bff_received" in body["timestamps"]:
                total_time = body["timestamps"]["db_committed"] - body["timestamps"]["bff_received"]
                print(f"[TIMING] Total end-to-end time: {total_time*1000:.2f}ms", flush=True)
                
                # Timestamps detallados
                consumer_delay = body["timestamps"]["consumer_received"] - body["timestamps"]["bff_received"]
                orders_processing = body["timestamps"]["db_committed"] - body["timestamps"]["orders_call_start"]
                print(f"[TIMING] BFF→SQS→Consumer: {consumer_delay*1000:.2f}ms", flush=True)
                print(f"[TIMING] Orders Service processing: {orders_processing*1000:.2f}ms", flush=True)
            
            return True
        except httpx.HTTPError as e:
            print(f"[MSG] HTTP error attempt {attempt + 1}: {e}", flush=True)
            # 5xx/timeout → reintentar una vez
            if attempt == 0:
                print(f"[MSG] Retrying in 1s...", flush=True)
                time.sleep(1.0)
                continue
            print(f"[MSG] ❌ Failed after 2 attempts", flush=True)
            return False
        except Exception as e:
            print(f"[MSG] Unexpected error attempt {attempt + 1}: {e}", flush=True)
            return False

def main():
    print(f"[MAIN] Consumer started, entering main loop...", flush=True)
    
    while True:
        try:
            print(f"[POLL] Polling SQS for messages (wait={WAIT}s)...", flush=True)
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
            print(f"[POLL] No messages received, continuing...", flush=True)
            continue
        
        print(f"[POLL] Received {len(msgs)} message(s)", flush=True)

        to_delete = []
        for i, m in enumerate(msgs):
            print(f"[BATCH] Processing message {i+1}/{len(msgs)}", flush=True)
            ok = False
            try:
                ok = handle_message(m)
            except Exception as e:
                print(f"[BATCH] handle_message error: {e}", flush=True)
            
            if ok:
                print(f"[BATCH] Message {i+1} processed successfully, marking for deletion", flush=True)
                to_delete.append({"Id": m["MessageId"], "ReceiptHandle": m["ReceiptHandle"]})
            else:
                print(f"[BATCH] Message {i+1} failed, will retry later", flush=True)

        if to_delete:
            try:
                print(f"[DELETE] Deleting {len(to_delete)} processed message(s)...", flush=True)
                sqs.delete_message_batch(QueueUrl=QUEUE_URL, Entries=to_delete)
                print(f"[DELETE] ✅ Successfully deleted {len(to_delete)} message(s)", flush=True)
            except (BotoCoreError, ClientError) as e:
                print(f"[DELETE] SQS delete error: {e}", flush=True)
        else:
            print(f"[DELETE] No messages to delete", flush=True)

if __name__ == "__main__":
    print(f"[START] Worker starting up...", flush=True)
    main()