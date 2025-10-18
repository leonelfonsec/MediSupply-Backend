from flask import Flask
from dotenv import load_dotenv
from .config import Config
from .services.sqs_client import SQSService
from .routes.health import bp as health_bp
from .routes.orders import bp as orders_bp
from .routes.rutas import bp as rutas_bp

def create_app():
    load_dotenv()               # carga variables desde .env si existe
    app = Flask(__name__)
    app.config.from_object(Config)

    # Registrar blueprints (rutas)
    app.register_blueprint(health_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(rutas_bp)

    # Inicializar servicio SQS y guardarlo en extensiones
    app.extensions["sqs"] = SQSService(
        region_name=app.config["AWS_REGION"],
        queue_url=app.config["SQS_QUEUE_URL"],
        default_group_id=app.config["MESSAGE_GROUP_ID"],
        content_based_dedup=app.config["CONTENT_BASED_DEDUP"]
    )
    return app