from flask import Blueprint, jsonify

bp = Blueprint("health", __name__)

@bp.get("/health")
def health():
    """
    Health check endpoint
    ---
    tags:
      - Health
    responses:
      200:
        description: Service is healthy
        schema:
          type: object
          properties:
            status:
              type: string
              example: "healthy"
            service:
              type: string
              example: "bff-venta"
    """
    return jsonify(status="ok"), 200