from flask import Blueprint, request, jsonify, current_app
import requests
from requests.exceptions import RequestException, Timeout
import os

bp = Blueprint("rutas", __name__)

def get_rutas_service_url():
    """Obtener la URL del servicio de rutas desde variables de entorno"""
    url = os.getenv("RUTAS_SERVICE_URL")
    if not url:
        current_app.logger.error("RUTAS_SERVICE_URL no está configurada")
        return None
    return url.rstrip('/')  # Remover trailing slash si existe


@bp.get("/api/v1/rutas/visita/<fecha>")
def get_ruta_by_fecha(fecha):
    """
    Obtener ruta de visita por fecha
    ---
    tags:
      - Rutas
    parameters:
      - in: path
        name: fecha
        type: string
        required: true
        description: Fecha en formato YYYY-MM-DD
        example: "2025-01-15"
    responses:
      200:
        description: Ruta encontrada
        schema:
          type: object
          properties:
            data:
              type: object
              description: Datos de la ruta
      404:
        description: Ruta no encontrada
      503:
        description: Servicio no disponible
      504:
        description: Timeout al consultar servicio
    """
    rutas_url = get_rutas_service_url()
    if not rutas_url:
        return jsonify(error="Servicio de rutas no disponible"), 503
    
    try:
        # Construir URL del servicio de rutas
        # Nota: Ajusta el path según lo que tenga tu servicio de rutas
        url = f"{rutas_url}/api/rutas/visita/{fecha}"
        
        current_app.logger.info(f"Calling rutas service: {url}")
        
        # Hacer request al servicio de rutas con timeout
        response = requests.get(
            url,
            timeout=10,  # 10 segundos timeout
            headers={
                "User-Agent": "BFF-Venta/1.0",
                "X-Request-ID": request.headers.get("X-Request-ID", "no-id"),
            }
        )
        
        # Si el servicio responde con error, propagar el error
        if response.status_code >= 400:
            current_app.logger.warning(
                f"Rutas service error: {response.status_code} - {response.text[:200]}"
            )
            
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text[:200]}
            
            return jsonify(
                error="Error al consultar ruta",
                details=error_data
            ), response.status_code
        
        # Respuesta exitosa
        current_app.logger.info(f"Rutas service success: {response.status_code}")
        
        try:
            return jsonify(response.json()), response.status_code
        except:
            return jsonify({"data": response.text}), response.status_code
        
    except Timeout:
        current_app.logger.error(f"Timeout al conectar con servicio de rutas: {rutas_url}")
        return jsonify(error="Timeout al consultar ruta"), 504
    
    except RequestException as e:
        current_app.logger.error(f"Error conectando con servicio de rutas: {e}")
        return jsonify(error="Error de conexión con servicio de rutas"), 503
    
    except Exception as e:
        current_app.logger.error(f"Error inesperado en rutas endpoint: {e}", exc_info=True)
        return jsonify(error="Error interno del servidor"), 500


@bp.get("/api/v1/rutas/health")
def rutas_health_check():
    """
    Health check del servicio de rutas
    ---
    tags:
      - Rutas
    responses:
      200:
        description: Servicio conectado
        schema:
          type: object
          properties:
            status:
              type: string
              example: "healthy"
            rutas_service:
              type: string
              example: "connected"
            rutas_url:
              type: string
      503:
        description: Servicio no disponible
    """
    rutas_url = get_rutas_service_url()
    
    if not rutas_url:
        return jsonify(
            status="unhealthy",
            reason="RUTAS_SERVICE_URL no configurada"
        ), 503
    
    try:
        response = requests.get(
            f"{rutas_url}/health",
            timeout=5
        )
        
        if response.status_code == 200:
            return jsonify(
                status="healthy",
                rutas_service="connected",
                rutas_url=rutas_url
            ), 200
        else:
            return jsonify(
                status="degraded",
                rutas_service="error",
                status_code=response.status_code,
                rutas_url=rutas_url
            ), 503
            
    except Timeout:
        return jsonify(
            status="unhealthy",
            rutas_service="timeout",
            rutas_url=rutas_url
        ), 503
    except Exception as e:
        return jsonify(
            status="unhealthy",
            rutas_service="disconnected",
            error=str(e),
            rutas_url=rutas_url
        ), 503