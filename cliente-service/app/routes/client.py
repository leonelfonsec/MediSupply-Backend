"""
Rutas API para cliente-service siguiendo patrón catalogo-service
Endpoints REST para HU07: Consultar Cliente
"""
import time
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.db import get_session
from app.services.client_service import ClienteService
from app.schemas import (
    ClienteBasicoResponse, HistoricoCompletoResponse,
    ErrorResponse
)
from app.config import get_settings

# Router para endpoints de cliente
router = APIRouter(prefix="/cliente", tags=["cliente"])
settings = get_settings()


@router.get("/",response_model=List[ClienteBasicoResponse],)
async def listar_clientes(
    request: Request,
    limite: int = Query(
        default=50,
        ge=1,
        le=500,
        description="Número máximo de clientes a retornar"
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Número de registros a saltar (para paginación)"
    ),
    activos_solo: bool = Query(
        default=True,
        description="Si mostrar solo clientes activos (true) o todos (false)"
    ),
    ordenar_por: str = Query(
        default="nombre",
        pattern="^(nombre|nit|codigo_unico|created_at)$",
        description="Campo por el cual ordenar los resultados"
    ),
    vendedor_id: Optional[str] = Query(
        None,
        min_length=1,
        max_length=64,
        description="ID del vendedor que realiza la consulta (para trazabilidad - opcional)"
    ),
    session: AsyncSession = Depends(get_session)
):
    """Listar todos los clientes disponibles con paginación y filtros"""
    started = time.perf_counter_ns()
    
    try:
        service = ClienteService(session, settings)
        clientes = await service.listar_clientes(
            limite=limite,
            offset=offset,
            activos_solo=activos_solo,
            ordenar_por=ordenar_por
        )
        
        # Medir performance
        took_ms = int((time.perf_counter_ns() - started) / 1_000_000)
        
        # Headers informativos siguiendo patrón catalogo
        headers = {
            "X-Response-Time-Ms": str(took_ms),
            "X-Total-Items": str(len(clientes)),
            "X-Limit": str(limite),
            "X-Offset": str(offset),
            "X-SLA-Compliant": str(took_ms <= settings.sla_max_response_ms)
        }
        
        return JSONResponse(
            content=[cliente.dict() for cliente in clientes],
            headers=headers
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "Error interno al listar clientes",
                "details": {"error_id": f"ERR_{int(time.time())}"},
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
            }
        )


@router.get(
    "/search",
    response_model=ClienteBasicoResponse,
    summary="Buscar cliente por NIT, nombre o código único",
    description="""
    Busca un cliente por NIT, nombre o código único.
    
    **Criterios de aceptación implementados:**
    - El vendedor puede buscar un cliente por NIT, nombre o código único
    - La consulta debe responder en ≤ 2 segundos  
    - La información consultada queda registrada para trazabilidad
    
    **Ejemplos de búsqueda:**
    - Por NIT: `900123456-7`
    - Por nombre: `Farmacia San José` 
    - Por código: `FSJ001`
    """
)
async def buscar_cliente(
    request: Request,
    q: str = Query(
        ...,
        min_length=2,
        max_length=255,
        description="NIT, nombre o código único del cliente a buscar"
    ),
    vendedor_id: str = Query(
        ...,
        min_length=1,
        max_length=64,
        description="ID del vendedor que realiza la consulta (para trazabilidad)"
    ),
    session: AsyncSession = Depends(get_session)
):
    """Buscar cliente por NIT, nombre o código único"""
    print(f"🔍 DEBUG: Iniciando buscar_cliente con q='{q}', vendedor_id='{vendedor_id}'")
    started = time.perf_counter_ns()
    
    try:
        print(f"🔍 DEBUG: Creando ClienteService...")
        service = ClienteService(session, settings)
        print(f"🔍 DEBUG: ClienteService creado, llamando buscar_cliente...")
        cliente = await service.buscar_cliente(
            termino_busqueda=q,
            vendedor_id=vendedor_id
        )
        print(f"🔍 DEBUG: Cliente encontrado: {cliente}")
        
        # Medir performance
        took_ms = int((time.perf_counter_ns() - started) / 1_000_000)
        
        # Headers informativos (usando Response para agregar headers)
        print(f"🔍 DEBUG: Añadiendo headers informativos - Response time: {took_ms}ms")
        
        # Usar response directo - FastAPI maneja la serialización automáticamente
        return cliente
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ DEBUG ERROR en buscar_cliente: {type(e).__name__}: {str(e)}")
        import traceback
        print(f"❌ DEBUG TRACEBACK: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "Error interno al buscar cliente",
                "details": {"error_id": f"ERR_{int(time.time())}"},
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
            }
        )


@router.get(
    "/{cliente_id}/historico",
    response_model=HistoricoCompletoResponse,
    summary="Obtener histórico completo del cliente",
    description="""
    Obtiene el histórico completo de un cliente incluyendo:
    
    **Criterios de aceptación implementados:**
    - Histórico de compras del cliente (productos, cantidades, fechas)
    - Productos preferidos y frecuencia de compra  
    - Devoluciones realizadas con sus motivos
    - La consulta debe responder en ≤ 2 segundos
    - La información consultada queda registrada para trazabilidad
    
    **Datos incluidos:**
    - 📋 Histórico de compras (últimos N meses)
    - ⭐ Productos preferidos con estadísticas
    - 🔄 Devoluciones con motivos
    - 📊 Estadísticas resumidas del cliente
    """
)
async def obtener_historico_cliente(
    request: Request,
    cliente_id: str = Path(
        ...,
        min_length=1,
        max_length=64,
        description="ID único del cliente"
    ),
    vendedor_id: str = Query(
        ...,
        min_length=1,
        max_length=64,
        description="ID del vendedor que realiza la consulta"
    ),
    limite_meses: int = Query(
        default=12,
        ge=1,
        le=60,
        description="Número de meses hacia atrás para el histórico (máximo 60)"
    ),
    incluir_devoluciones: bool = Query(
        default=True,
        description="Si incluir o no las devoluciones en el histórico"
    ),
    session: AsyncSession = Depends(get_session)
):
    """Obtener histórico completo del cliente"""
    started = time.perf_counter_ns()
    
    try:
        service = ClienteService(session, settings)
        historico = await service.obtener_historico_completo(
            cliente_id=cliente_id,
            vendedor_id=vendedor_id,
            limite_meses=limite_meses,
            incluir_devoluciones=incluir_devoluciones
        )
        
        # Medir performance
        took_ms = int((time.perf_counter_ns() - started) / 1_000_000)
        
        # Headers informativos
        headers = {
            "X-Response-Time-Ms": str(took_ms),
            "X-SLA-Compliant": str(took_ms <= settings.sla_max_response_ms),
            "X-Service": "cliente-service"
        }
        
        return JSONResponse(
            content=historico.dict(),
            headers=headers
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "Error interno al obtener histórico del cliente",
                "details": {
                    "cliente_id": cliente_id,
                    "error_id": f"ERR_{int(time.time())}"
                },
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
            }
        )


@router.get(
    "/health",
    summary="Health check del servicio",
    description="Endpoint de health check para verificar el estado del servicio"
)
async def health_check(request: Request):
    """Health check del servicio"""
    return {
        "status": "healthy",
        "service": "cliente-service",
        "version": "1.0.0",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sla_max_response_ms": settings.sla_max_response_ms,
        "database": "connected"
    }


@router.get(
    "/metrics",
    summary="Métricas del servicio",
    description="Obtener métricas básicas del servicio cliente"
)
async def get_metrics(
    request: Request,
    session: AsyncSession = Depends(get_session)
):
    """Obtener métricas del servicio"""
    try:
        service = ClienteService(session, settings)
        metrics = await service.obtener_metricas()
        
        return JSONResponse(
            content=metrics,
            headers={
                "X-Service": "cliente-service",
                "X-Generated-At": time.strftime("%Y-%m-%dT%H:%M:%SZ")
            }
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": "METRICS_ERROR",
                "message": "Error al obtener métricas",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
            }
        )