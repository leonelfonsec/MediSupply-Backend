from flask import Blueprint, request, jsonify, current_app
import uuid
from concurrent.futures import ThreadPoolExecutor
import threading
import time

bp = Blueprint("orders", __name__)

# Thread pool global para operaciones I/O
executor = ThreadPoolExecutor(max_workers=10)

@bp.post("/api/v1/orders")
def post_message():
    data = request.get_json(silent=True) or {}
    body = data.get("body")
    if not body:
        return jsonify(error="Falta 'body' en el JSON"), 400
    
    event_id = str(uuid.uuid4())
    sqs_message = {
        "event_id": event_id,
        "order": body,
        "timestamps": {
            "bff_received": time.time(),
            "sqs_sent": time.time()
        }
    }

    group_id = data.get("group_id")
    dedup_id = data.get("dedup_id", event_id)

    sqs: "SQSService" = current_app.extensions["sqs"]
    
    # Enviar a SQS de forma asíncrona (no bloqueante)
    future = executor.submit(
        send_sqs_message_async, 
        sqs, 
        sqs_message, 
        group_id, 
        dedup_id
    )
    
    # Respuesta inmediata sin esperar SQS
    return jsonify(
        messageId=f"async-{event_id}",  # ID temporal
        event_id=event_id,
        status="accepted"
    ), 202

def send_sqs_message_async(sqs, message, group_id, dedup_id):
    """Función para enviar mensaje a SQS en background"""
    try:
        resp = sqs.send_message(body=message, group_id=group_id, dedup_id=dedup_id)
        current_app.logger.info(f"SQS message sent: {resp['MessageId']}")
        return resp
    except Exception as e:
        current_app.logger.error(f"Error sending SQS message: {e}")
        # Aquí podrías implementar retry logic o DLQ