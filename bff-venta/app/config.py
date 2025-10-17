import os

class Config:
    # Región y cola (ajústalo a tu caso)
    AWS_REGION = os.getenv("AWS_REGION", "us-east-2")
    SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL")  # p.ej. https://sqs.us-east-2.amazonaws.com/4117.../prueba-cola.fifo

    # Para FIFO
    MESSAGE_GROUP_ID = os.getenv("MESSAGE_GROUP_ID", "grupo1")
    CONTENT_BASED_DEDUP = os.getenv("CONTENT_BASED_DEDUP", "true").lower() == "true"

    # Para LocalStack
    AWS_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL")  # http://localhost:4566

    # Flask
    JSON_SORT_KEYS = False