"""
Repositorio de Cliente siguiendo patrón catalogo-service
Capa de acceso a datos para HU07: Consultar Cliente
"""
from sqlalchemy import select, func, and_, desc, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta

from app.models.client_model import (
    Cliente, CompraHistorico, DevolucionHistorico, 
    ConsultaClienteLog, ProductoPreferido, EstadisticaCliente
)
from app.schemas import ClienteBasicoResponse


class ClienteRepository:
    """Repositorio para operaciones de base de datos de clientes"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def listar_clientes(
        self,
        limite: int = 50,
        offset: int = 0,
        activos_solo: bool = True,
        ordenar_por: str = "nombre"
    ) -> List[ClienteBasicoResponse]:
        """Listar clientes con paginación y filtros"""
        
        # Construir query base
        stmt = select(Cliente)
        
        # Filtrar por activos si se solicita
        if activos_solo:
            stmt = stmt.where(Cliente.activo.is_(True))
        
        # Ordenamiento
        if ordenar_por == "nombre":
            stmt = stmt.order_by(Cliente.nombre.asc())
        elif ordenar_por == "nit":
            stmt = stmt.order_by(Cliente.nit.asc())
        elif ordenar_por == "codigo_unico":
            stmt = stmt.order_by(Cliente.codigo_unico.asc())
        elif ordenar_por == "created_at":
            stmt = stmt.order_by(desc(Cliente.created_at))
        else:
            stmt = stmt.order_by(Cliente.nombre.asc())  # Default
        
        # Paginación
        stmt = stmt.offset(offset).limit(limite)
        
        # Ejecutar query
        result = await self.session.execute(stmt)
        clientes = result.scalars().all()
        
        # Convertir a response models
        clientes_response = []
        for cliente in clientes:
            clientes_response.append(ClienteBasicoResponse(
                id=cliente.id,
                nit=cliente.nit,
                nombre=cliente.nombre,
                codigo_unico=cliente.codigo_unico,
                email=cliente.email,
                telefono=cliente.telefono,
                ciudad=cliente.ciudad,
                pais=cliente.pais,
                activo=cliente.activo
            ))
        
        return clientes_response
    
    async def buscar_cliente_por_termino(self, termino: str) -> Optional[Cliente]:
        """
        Buscar cliente por NIT, nombre o código único
        Implementa búsqueda flexible como requiere HU07
        """
        print(f"🔍 REPOSITORY DEBUG: Iniciando buscar_cliente_por_termino con termino='{termino}'")
        # Limpiar término de búsqueda
        termino_limpio = termino.strip()
        print(f"🔍 REPOSITORY DEBUG: Término limpio: '{termino_limpio}'")
        
        print(f"🔍 REPOSITORY DEBUG: Verificando término vacío...")
        if not termino_limpio:
            print(f"🔍 REPOSITORY DEBUG: Término vacío, retornando None")
            return None
        
        print(f"🔍 REPOSITORY DEBUG: Creando query base...")
        # Query base
        stmt = select(Cliente).where(Cliente.activo.is_(True))
        print(f"🔍 REPOSITORY DEBUG: Query base creada exitosamente")
        
        # Construir condiciones de búsqueda (OR logic)
        condiciones = []
        
        # Búsqueda exacta por NIT
        condiciones.append(Cliente.nit == termino_limpio)
        
        # Búsqueda exacta por código único
        condiciones.append(Cliente.codigo_unico == termino_limpio)
        
        # Búsqueda por nombre (parcial, case-insensitive)
        condiciones.append(func.lower(Cliente.nombre).like(f"%{termino_limpio.lower()}%"))
        
        # Si el término parece un NIT parcial (solo números), buscar por NIT parcial
        if termino_limpio.replace('-', '').isdigit():
            condiciones.append(Cliente.nit.like(f"%{termino_limpio}%"))
        
        # Aplicar condiciones con OR
        print(f"🔍 REPOSITORY DEBUG: Usando sesión existente...")
        try:
            print(f"🔍 REPOSITORY DEBUG: Importando or_...")
            from sqlalchemy import or_
            print(f"🔍 REPOSITORY DEBUG: or_ importado, aplicando condiciones...")
            stmt = stmt.where(or_(*condiciones))
            print(f"🔍 REPOSITORY DEBUG: Condiciones aplicadas, ejecutando query...")
            
            # Ejecutar query (tomar el primer resultado)
            result = await self.session.execute(stmt)
            print(f"🔍 REPOSITORY DEBUG: Query ejecutada, obteniendo resultado...")
            cliente = result.scalars().first()
            print(f"🔍 REPOSITORY DEBUG: Cliente encontrado: {cliente is not None}")
            return cliente
        except Exception as e:
            print(f"🔍 REPOSITORY DEBUG: Error en buscar_cliente_por_termino: {e}")
            import traceback
            print(f"🔍 REPOSITORY DEBUG: Traceback: {traceback.format_exc()}")
            raise
    
    async def obtener_historico_completo(
        self, 
        cliente_id: str,
        limite_meses: int = 12,
        incluir_devoluciones: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Obtener histórico completo del cliente
        Implementa todos los criterios de HU07
        """
        print(f"🔍 REPOSITORY DEBUG: Iniciando obtener_historico_completo para cliente_id='{cliente_id}'")
        try:
            print(f"🔍 REPOSITORY DEBUG: Usando sesión existente, verificando si cliente existe...")
            # Verificar que el cliente existe
            cliente_stmt = select(Cliente).where(Cliente.id == cliente_id)
            cliente_result = await self.session.execute(cliente_stmt)
            cliente = cliente_result.scalars().first()
            
            print(f"🔍 REPOSITORY DEBUG: Cliente encontrado: {cliente is not None}")
            if not cliente:
                print(f"🔍 REPOSITORY DEBUG: Cliente no encontrado, retornando None")
                return None
        except Exception as e:
            print(f"🔍 REPOSITORY DEBUG: Error en obtener_historico_completo: {e}")
            import traceback
            print(f"🔍 REPOSITORY DEBUG: Traceback: {traceback.format_exc()}")
            raise
        
        # Calcular fecha límite
        fecha_limite = date.today() - timedelta(days=limite_meses * 30)
        
        # 1. Obtener histórico de compras
        compras_stmt = select(CompraHistorico).where(
            and_(
                CompraHistorico.cliente_id == cliente_id,
                CompraHistorico.fecha_compra >= fecha_limite
            )
        ).order_by(desc(CompraHistorico.fecha_compra))
        
        compras_result = await self.session.execute(compras_stmt)
        compras = compras_result.scalars().all()
        
        # 2. Obtener devoluciones si se solicitan
        devoluciones = []
        if incluir_devoluciones:
            dev_stmt = select(DevolucionHistorico).where(
                and_(
                    DevolucionHistorico.cliente_id == cliente_id,
                    DevolucionHistorico.fecha_devolucion >= fecha_limite
                )
            ).order_by(desc(DevolucionHistorico.fecha_devolucion))
            
            dev_result = await self.session.execute(dev_stmt)
            devoluciones = dev_result.scalars().all()
        
        # 3. Calcular productos preferidos
        productos_preferidos = await self._calcular_productos_preferidos(cliente_id, fecha_limite)
        
        # 4. Calcular estadísticas
        estadisticas = await self._calcular_estadisticas_cliente(cliente_id, compras, devoluciones)
        
        # Construir respuesta
        return {
            "cliente": ClienteBasicoResponse(
                id=cliente.id,
                nit=cliente.nit,
                nombre=cliente.nombre,
                codigo_unico=cliente.codigo_unico,
                email=cliente.email,
                telefono=cliente.telefono,
                ciudad=cliente.ciudad,
                pais=cliente.pais,
                activo=cliente.activo
            ),
            "historico_compras": [
                {
                    "orden_id": compra.orden_id,
                    "producto_id": compra.producto_id,
                    "producto_nombre": compra.producto_nombre,
                    "categoria_producto": compra.categoria_producto,
                    "cantidad": compra.cantidad,
                    "precio_unitario": str(compra.precio_unitario),
                    "precio_total": str(compra.precio_total),
                    "fecha_compra": compra.fecha_compra.isoformat(),
                    "estado_orden": compra.estado_orden
                }
                for compra in compras
            ],
            "productos_preferidos": productos_preferidos,
            "devoluciones": [
                {
                    "id": dev.id,
                    "compra_orden_id": dev.compra_orden_id,
                    "producto_id": dev.producto_id,
                    "producto_nombre": dev.producto_nombre,
                    "cantidad_devuelta": dev.cantidad_devuelta,
                    "motivo": dev.motivo,
                    "categoria_motivo": dev.categoria_motivo,
                    "fecha_devolucion": dev.fecha_devolucion.isoformat(),
                    "estado": dev.estado
                }
                for dev in devoluciones
            ],
            "estadisticas": estadisticas
        }
    
    async def _calcular_productos_preferidos(
        self, 
        cliente_id: str, 
        fecha_limite: date
    ) -> List[Dict[str, Any]]:
        """Calcular productos preferidos basado en frecuencia de compra"""
        
        # Query para agrupar por producto y calcular estadísticas
        stmt = select(
            CompraHistorico.producto_id,
            CompraHistorico.producto_nombre,
            CompraHistorico.categoria_producto,
            func.count(CompraHistorico.id).label("frecuencia_compra"),
            func.sum(CompraHistorico.cantidad).label("cantidad_total"),
            func.avg(CompraHistorico.cantidad).label("cantidad_promedio"),
            func.max(CompraHistorico.fecha_compra).label("ultima_compra")
        ).where(
            and_(
                CompraHistorico.cliente_id == cliente_id,
                CompraHistorico.fecha_compra >= fecha_limite
            )
        ).group_by(
            CompraHistorico.producto_id,
            CompraHistorico.producto_nombre,
            CompraHistorico.categoria_producto
        ).order_by(
            desc("frecuencia_compra"),
            desc("cantidad_total")
        ).limit(10)  # Top 10 productos preferidos
        
        result = await self.session.execute(stmt)
        productos_stats = result.all()
        
        productos_preferidos = []
        for stats in productos_stats:
            # Calcular meses desde última compra
            meses_desde_ultima = (date.today() - stats.ultima_compra).days // 30
            
            productos_preferidos.append({
                "producto_id": stats.producto_id,
                "producto_nombre": stats.producto_nombre,
                "categoria_producto": stats.categoria_producto,
                "frecuencia_compra": stats.frecuencia_compra,
                "cantidad_total": stats.cantidad_total,
                "cantidad_promedio": float(stats.cantidad_promedio or 0),
                "ultima_compra": stats.ultima_compra.isoformat(),
                "meses_desde_ultima_compra": meses_desde_ultima
            })
        
        return productos_preferidos
    
    async def _calcular_estadisticas_cliente(
        self, 
        cliente_id: str, 
        compras: List[CompraHistorico], 
        devoluciones: List[DevolucionHistorico]
    ) -> Dict[str, Any]:
        """Calcular estadísticas resumidas del cliente"""
        
        if not compras:
            return {
                "total_compras": 0,
                "total_productos_unicos": 0,
                "total_devoluciones": len(devoluciones),
                "valor_total_compras": "0.00",
                "promedio_orden": "0.00",
                "frecuencia_compra_mensual": 0.0,
                "tasa_devolucion": 0.0,
                "cliente_desde": None,
                "ultima_compra": None
            }
        
        # Calcular valores agregados
        total_compras = len(compras)
        productos_unicos = len(set(compra.producto_id for compra in compras))
        valor_total = sum(compra.precio_total for compra in compras)
        promedio_orden = valor_total / total_compras if total_compras > 0 else 0
        
        # Calcular frecuencia mensual
        primera_compra = min(compra.fecha_compra for compra in compras)
        ultima_compra = max(compra.fecha_compra for compra in compras)
        dias_activo = (ultima_compra - primera_compra).days or 1
        meses_activo = max(dias_activo / 30, 1)
        frecuencia_mensual = total_compras / meses_activo
        
        # Calcular tasa de devolución
        total_devoluciones = len(devoluciones)
        tasa_devolucion = (total_devoluciones / total_compras * 100) if total_compras > 0 else 0
        
        return {
            "total_compras": total_compras,
            "total_productos_unicos": productos_unicos,
            "total_devoluciones": total_devoluciones,
            "valor_total_compras": str(valor_total),
            "promedio_orden": str(promedio_orden),
            "frecuencia_compra_mensual": round(frecuencia_mensual, 2),
            "tasa_devolucion": round(tasa_devolucion, 1),
            "cliente_desde": primera_compra.isoformat(),
            "ultima_compra": ultima_compra.isoformat()
        }
    
    async def registrar_consulta(
        self,
        vendedor_id: str,
        cliente_id: str,
        tipo_consulta: str,
        tipo_busqueda: str = None,
        termino_busqueda: str = None,
        took_ms: int = None,
        metadatos: Dict[str, Any] = None
    ):
        """Registrar consulta para trazabilidad (criterio de HU07)"""
        
        try:
            log_entry = ConsultaClienteLog(
                vendedor_id=vendedor_id,
                cliente_id=cliente_id,
                tipo_consulta=tipo_consulta,
                tipo_busqueda=tipo_busqueda,
                termino_busqueda=termino_busqueda,
                took_ms=took_ms,
                metadatos=metadatos or {},
                fecha_consulta=datetime.utcnow()
            )
            
            self.session.add(log_entry)
            await self.session.commit()
            
        except Exception as e:
            # No fallar la operación principal si el logging falla
            await self.session.rollback()
            print(f"Warning: No se pudo registrar consulta de trazabilidad: {e}")
    
    async def contar_clientes(self) -> int:
        """Contar total de clientes"""
        stmt = select(func.count(Cliente.id))
        result = await self.session.execute(stmt)
        return result.scalar_one()
    
    async def contar_clientes_activos(self) -> int:
        """Contar clientes activos"""
        stmt = select(func.count(Cliente.id)).where(Cliente.activo.is_(True))
        result = await self.session.execute(stmt)
        return result.scalar_one()
    
    async def contar_consultas_hoy(self) -> int:
        """Contar consultas realizadas hoy"""
        hoy = date.today()
        stmt = select(func.count(ConsultaClienteLog.id)).where(
            func.date(ConsultaClienteLog.fecha_consulta) == hoy
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()