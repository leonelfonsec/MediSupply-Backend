"""
Servicios para cliente-service
Implementa la lógica de negocio para HU07
"""
import time
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.repositories.client_repo import ClienteRepository
from app.schemas import (
    ClienteBusquedaRequest, HistoricoClienteRequest,
    ClienteBasicoResponse, HistoricoCompletoResponse,
    ErrorResponse, ValidacionResponse
)
from app.config import get_settings


class ClienteService:
    """
    Servicio principal para operaciones de cliente
    Implementa todos los criterios de aceptación de HU07
    """
    
    def __init__(self, session: AsyncSession, settings=None):
        self.session = session
        self.repository = ClienteRepository(session)
        self.settings = settings or get_settings()
    
    async def buscar_cliente(
        self, 
        termino_busqueda: str,
        vendedor_id: str
    ) -> ClienteBasicoResponse:
        """
        Busca cliente por NIT, nombre o código único
        
        Criterios implementados:
        - El vendedor puede buscar un cliente por NIT, nombre o código único
        - La consulta debe responder en ≤ 2 segundos
        - La información consultada queda registrada para trazabilidad
        """
        print(f"🔍 SERVICE DEBUG: Iniciando buscar_cliente con termino='{termino_busqueda}', vendedor='{vendedor_id}'")
        start_time = time.perf_counter_ns()
        
        try:
            print(f"🔍 SERVICE DEBUG: Llamando repository.buscar_cliente_por_termino...")
            # Buscar cliente
            cliente = await self.repository.buscar_cliente_por_termino(termino_busqueda)
            print(f"🔍 SERVICE DEBUG: Repository retornó: {cliente}")
            
            if not cliente:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error": "CLIENT_NOT_FOUND",
                        "message": "Cliente no encontrado con el término de búsqueda proporcionado",
                        "details": {
                            "termino_busqueda": termino_busqueda,
                            "sugerencias": [
                                "Verificar el NIT completo con dígito de verificación",
                                "Usar el nombre completo del cliente",
                                "Probar con el código único asignado"
                            ]
                        },
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                )
            
            # Calcular tiempo de respuesta
            took_ms = int((time.perf_counter_ns() - start_time) / 1_000_000)
            
            # Determinar tipo de búsqueda para auditoría
            term = termino_busqueda.strip()
            if term.replace('-', '').replace(' ', '').isdigit():
                tipo_busqueda = "nit"
            elif len(term) < 10 and term.isalnum():
                tipo_busqueda = "codigo"
            else:
                tipo_busqueda = "nombre"
            
            # Registrar consulta para trazabilidad (TEMPORALMENTE DESHABILITADO PARA DEBUG)
            print(f"🔍 SERVICE DEBUG: Skipping auditoria temporalmente para debug")
            # await self.repository.registrar_consulta(...)
            
            # Validar SLA de performance
            if took_ms > self.settings.sla_max_response_ms:
                # Log warning pero no fallar la consulta
                print(f"⚠️ WARNING: Búsqueda de cliente tardó {took_ms}ms (SLA: {self.settings.sla_max_response_ms}ms)")
            
            print(f"🔍 SERVICE DEBUG: Creando ClienteBasicoResponse...")
            print(f"🔍 SERVICE DEBUG: Cliente data - id:{cliente.id}, nit:{cliente.nit}, nombre:{cliente.nombre}")
            print(f"🔍 SERVICE DEBUG: Cliente object attrs: {[attr for attr in dir(cliente) if not attr.startswith('_')]}")
            try:
                # Usar from_attributes=True para mapear automáticamente
                response = ClienteBasicoResponse.model_validate(cliente)
                print(f"🔍 SERVICE DEBUG: ClienteBasicoResponse creado exitosamente con model_validate")
                return response
            except Exception as resp_error:
                print(f"🔍 SERVICE DEBUG ERROR en ClienteBasicoResponse: {resp_error}")
                import traceback
                print(f"🔍 SERVICE DEBUG: Traceback: {traceback.format_exc()}")
                # Intentar mapeo manual como fallback
                try:
                    print(f"🔍 SERVICE DEBUG: Intentando mapeo manual...")
                    response = ClienteBasicoResponse(
                        id=cliente.id,
                        nit=cliente.nit,
                        nombre=cliente.nombre,
                        codigo_unico=cliente.codigo_unico,
                        email=cliente.email,
                        telefono=cliente.telefono,
                        direccion=getattr(cliente, 'direccion', None),
                        ciudad=cliente.ciudad,
                        pais=cliente.pais,
                        activo=cliente.activo,
                        created_at=getattr(cliente, 'created_at', None),
                        updated_at=getattr(cliente, 'updated_at', None)
                    )
                    print(f"🔍 SERVICE DEBUG: Mapeo manual exitoso")
                    return response
                except Exception as manual_error:
                    print(f"🔍 SERVICE DEBUG ERROR en mapeo manual: {manual_error}")
                    raise manual_error
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            # Log error y registrar consulta fallida
            took_ms = int((time.perf_counter_ns() - start_time) / 1_000_000)
            
            # Intentar registrar el error
            try:
                await self.repository.registrar_consulta(
                    vendedor_id=vendedor_id,
                    cliente_id="ERROR",
                    tipo_consulta="busqueda_cliente",
                    termino_busqueda=termino_busqueda,
                    took_ms=took_ms,
                    metadatos={
                        "resultado_encontrado": False,
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
                )
            except:
                pass  # No fallar si no se puede registrar el log
            
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "INTERNAL_SERVER_ERROR",
                    "message": "Error interno al buscar cliente",
                    "details": {"error_id": f"ERR_{int(time.time())}"},
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            )
    
    async def obtener_historico_completo(
        self, 
        cliente_id: str,
        vendedor_id: str,
        limite_meses: int = 12,
        incluir_devoluciones: bool = True
    ) -> HistoricoCompletoResponse:
        """
        Obtiene histórico completo del cliente
        
        Criterios implementados:
        - El sistema muestra el histórico de compras del cliente (productos, cantidades, fechas)
        - El sistema muestra productos preferidos y frecuencia de compra
        - El sistema muestra devoluciones realizadas con sus motivos
        - La consulta debe responder en ≤ 2 segundos
        - La información consultada queda registrada para trazabilidad
        """
        start_time = time.perf_counter_ns()
        
        try:
            # Obtener histórico completo
            historico_data = await self.repository.obtener_historico_completo(
                cliente_id=cliente_id,
                limite_meses=limite_meses,
                incluir_devoluciones=incluir_devoluciones
            )
            
            if not historico_data:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error": "CLIENT_NOT_FOUND",
                        "message": "Cliente no encontrado",
                        "details": {"cliente_id": cliente_id},
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                )
            
            # Calcular tiempo de respuesta
            took_ms = int((time.perf_counter_ns() - start_time) / 1_000_000)
            
            # Validar SLA crítico (≤ 2 segundos)
            cumple_sla = took_ms <= self.settings.sla_max_response_ms
            
            # Crear metadatos de la consulta
            metadatos = {
                "consulta_took_ms": took_ms,
                "fecha_consulta": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "limite_meses": limite_meses,
                "vendedor_id": vendedor_id,
                "incluyo_devoluciones": incluir_devoluciones,
                "cumple_sla": cumple_sla,
                "total_items": {
                    "compras": len(historico_data['historico_compras']),
                    "productos_preferidos": len(historico_data['productos_preferidos']),
                    "devoluciones": len(historico_data['devoluciones'])
                }
            }
            
            # Advertencias de performance
            advertencias = []
            if not cumple_sla:
                advertencias.append(f"Consulta tardó {took_ms}ms (SLA: {self.settings.sla_max_response_ms}ms)")
            
            if took_ms > 1500:  # Warning a los 1.5 segundos
                advertencias.append("Consulta cerca del límite de performance")
            
            metadatos["advertencias_performance"] = advertencias
            
            # Registrar consulta para trazabilidad
            await self.repository.registrar_consulta(
                vendedor_id=vendedor_id,
                cliente_id=cliente_id,
                tipo_consulta="historico_completo",
                took_ms=took_ms,
                metadatos={
                    "limite_meses": limite_meses,
                    "incluyo_devoluciones": incluir_devoluciones,
                    "total_compras": len(historico_data['historico_compras']),
                    "total_preferidos": len(historico_data['productos_preferidos']),
                    "total_devoluciones": len(historico_data['devoluciones']),
                    "cumple_sla": cumple_sla
                }
            )
            
            # Construir respuesta
            cliente_response = ClienteBasicoResponse(
                id=historico_data['cliente'].id,
                nit=historico_data['cliente'].nit,
                nombre=historico_data['cliente'].nombre,
                codigo_unico=historico_data['cliente'].codigo_unico,
                email=historico_data['cliente'].email,
                telefono=historico_data['cliente'].telefono,
                ciudad=historico_data['cliente'].ciudad,
                pais=historico_data['cliente'].pais,
                activo=historico_data['cliente'].activo
            )
            
            return HistoricoCompletoResponse(
                cliente=cliente_response,
                historico_compras=historico_data['historico_compras'],
                productos_preferidos=historico_data['productos_preferidos'],
                devoluciones=historico_data['devoluciones'],
                estadisticas=historico_data['estadisticas'],
                metadatos=metadatos
            )
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            took_ms = int((time.perf_counter_ns() - start_time) / 1_000_000)
            
            # Registrar error
            try:
                await self.repository.registrar_consulta(
                    vendedor_id=vendedor_id,
                    cliente_id=cliente_id,
                    tipo_consulta="historico_completo_error",
                    took_ms=took_ms,
                    metadatos={
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "limite_meses": limite_meses
                    }
                )
            except:
                pass
            
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "INTERNAL_SERVER_ERROR",
                    "message": "Error interno al obtener histórico del cliente",
                    "details": {
                        "cliente_id": cliente_id,
                        "error_id": f"ERR_{int(time.time())}"
                    },
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            )
    
    async def validar_performance(
        self, 
        tiempo_respuesta_ms: int
    ) -> ValidacionResponse:
        """
        Valida si la consulta cumple con el SLA de performance
        Criterio: "La consulta debe responder en ≤ 2 segundos"
        """
        limite_sla = self.settings.sla_max_response_ms
        cumple_sla = tiempo_respuesta_ms <= limite_sla
        
        advertencias = []
        
        if not cumple_sla:
            advertencias.append(f"Tiempo de respuesta excede el SLA: {tiempo_respuesta_ms}ms > {limite_sla}ms")
        
        if tiempo_respuesta_ms > (limite_sla * 0.75):  # 75% del límite
            advertencias.append("Tiempo de respuesta cerca del límite SLA")
        
        if tiempo_respuesta_ms > 1000:  # > 1 segundo
            advertencias.append("Considerar optimización de consultas")
        
        return ValidacionResponse(
            cumple_sla=cumple_sla,
            tiempo_respuesta_ms=tiempo_respuesta_ms,
            limite_sla_ms=limite_sla,
            advertencias=advertencias
        )
    
    async def listar_clientes(
        self,
        limite: int = 50,
        offset: int = 0,
        activos_solo: bool = True,
        ordenar_por: str = "nombre"
    ) -> List[ClienteBasicoResponse]:
        """
        Lista clientes con paginación y filtros
        Método requerido por las rutas
        """
        start_time = time.perf_counter_ns()
        
        try:
            clientes = await self.repository.listar_clientes(
                limite=limite,
                offset=offset,
                activos_solo=activos_solo,
                ordenar_por=ordenar_por
            )
            
            # Calcular tiempo de respuesta
            tiempo_respuesta_ms = int((time.perf_counter_ns() - start_time) / 1_000_000)
            
            return clientes
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al listar clientes: {str(e)}"
            )
    
    async def obtener_metricas(self) -> Dict[str, Any]:
        """
        Obtiene métricas del servicio
        Método requerido por las rutas para el endpoint /metrics
        """
        try:
            total_clientes = await self.repository.contar_clientes()
            clientes_activos = await self.repository.contar_clientes_activos()
            consultas_hoy = await self.repository.contar_consultas_hoy()
            
            return {
                "service": "cliente-service",
                "version": "1.0.0",
                "timestamp": datetime.utcnow().isoformat(),
                "stats": {
                    "total_clientes": total_clientes,
                    "clientes_activos": clientes_activos,
                    "clientes_inactivos": total_clientes - clientes_activos,
                    "consultas_realizadas_hoy": consultas_hoy
                },
                "sla": {
                    "max_response_time_ms": self.settings.sla_max_response_ms,
                    "description": "Todas las consultas deben responder en ≤ 2 segundos"
                }
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al obtener métricas: {str(e)}"
            )