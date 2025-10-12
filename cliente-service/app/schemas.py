"""
Esquemas Pydantic para cliente-service
Payloads de entrada y salida para la HU07: Consultar Cliente
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from decimal import Decimal


# ==========================================
# ESQUEMAS DE ENTRADA (REQUEST PAYLOADS)
# ==========================================

class ClienteBusquedaRequest(BaseModel):
    """Payload para búsqueda de cliente por NIT, nombre o código único"""
    termino_busqueda: str = Field(
        ..., 
        min_length=2, 
        max_length=255,
        description="NIT, nombre o código único del cliente a buscar",
        example="900123456-7"
    )
    vendedor_id: str = Field(
        ..., 
        min_length=1, 
        max_length=64,
        description="ID del vendedor que realiza la consulta (para trazabilidad)",
        example="VEN001"
    )
    
    @field_validator('termino_busqueda')
    @classmethod
    def validar_termino_busqueda(cls, v):
        if not v or v.strip() == "":
            raise ValueError("El término de búsqueda no puede estar vacío")
        return v.strip()


class HistoricoClienteRequest(BaseModel):
    """Payload para consultar histórico completo de un cliente"""
    cliente_id: str = Field(
        ..., 
        min_length=1, 
        max_length=64,
        description="ID único del cliente",
        example="CLI001"
    )
    vendedor_id: str = Field(
        ..., 
        min_length=1, 
        max_length=64,
        description="ID del vendedor que realiza la consulta",
        example="VEN001"
    )
    incluir_devoluciones: bool = Field(
        default=True,
        description="Si incluir o no las devoluciones en el histórico"
    )
    limite_meses: int = Field(
        default=12,
        ge=1,
        le=60,
        description="Número de meses hacia atrás para el histórico (máximo 60)"
    )


# ==========================================
# ESQUEMAS DE SALIDA (RESPONSE PAYLOADS)
# ==========================================

class ClienteBasicoResponse(BaseModel):
    """Información básica del cliente encontrado en la búsqueda"""
    id: str = Field(..., description="ID único del cliente")
    nit: str = Field(..., description="NIT del cliente")
    nombre: str = Field(..., description="Nombre completo del cliente")
    codigo_unico: str = Field(..., description="Código único del cliente")
    email: Optional[str] = Field(None, description="Email del cliente")
    telefono: Optional[str] = Field(None, description="Teléfono del cliente")
    direccion: Optional[str] = Field(None, description="Dirección del cliente")
    ciudad: Optional[str] = Field(None, description="Ciudad del cliente")
    pais: Optional[str] = Field(None, description="País del cliente")
    activo: bool = Field(default=True, description="Si el cliente está activo")
    created_at: Optional[datetime] = Field(None, description="Fecha de creación")
    updated_at: Optional[datetime] = Field(None, description="Fecha de última actualización")
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "CLI001",
                "nit": "900123456-7",
                "nombre": "Farmacia San José",
                "codigo_unico": "FSJ001",
                "email": "contacto@farmaciasanjose.com",
                "telefono": "+57-1-2345678",
                "direccion": "Calle 123 #45-67",
                "ciudad": "Bogotá",
                "pais": "CO",
                "activo": True,
                "created_at": "2023-06-15T10:30:00Z",
                "updated_at": "2024-09-15T10:30:00Z"
            }
        }
    }


class CompraHistoricoItem(BaseModel):
    """Item individual del histórico de compras"""
    id: str = Field(..., description="ID del registro de compra")
    orden_id: str = Field(..., description="ID de la orden de compra")
    producto_id: str = Field(..., description="ID del producto comprado")
    producto_nombre: str = Field(..., description="Nombre del producto")
    categoria_producto: Optional[str] = Field(None, description="Categoría del producto")
    cantidad: int = Field(..., ge=1, description="Cantidad comprada")
    precio_unitario: Decimal = Field(..., description="Precio unitario del producto")
    precio_total: Decimal = Field(..., description="Precio total de la línea")
    fecha_compra: date = Field(..., description="Fecha de la compra")
    estado_orden: Optional[str] = Field(None, description="Estado de la orden")
    created_at: Optional[datetime] = Field(None, description="Fecha de creación del registro")
    
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            Decimal: lambda v: float(v)
        },
        "json_schema_extra": {
            "example": {
                "id": "CH001",
                "orden_id": "ORD001",
                "producto_id": "PROD123",
                "producto_nombre": "Acetaminofén 500mg",
                "categoria_producto": "Analgésicos",
                "cantidad": 100,
                "precio_unitario": 150.50,
                "precio_total": 15050.00,
                "fecha_compra": "2024-09-15",
                "estado_orden": "completada",
                "created_at": "2024-09-15T10:30:00Z"
            }
        }
    }


class ProductoPreferidoItem(BaseModel):
    """Producto preferido con estadísticas de compra"""
    id: str = Field(..., description="ID del registro")
    cliente_id: str = Field(..., description="ID del cliente")
    producto_id: str = Field(..., description="ID del producto")
    producto_nombre: str = Field(..., description="Nombre del producto")
    categoria_producto: Optional[str] = Field(None, description="Categoría del producto")
    frecuencia_compra: int = Field(..., ge=1, description="Número de veces comprado")
    cantidad_total: int = Field(..., ge=1, description="Cantidad total comprada")
    cantidad_promedio: Decimal = Field(..., ge=0, description="Cantidad promedio por compra")
    ultima_compra: Optional[date] = Field(None, description="Fecha de la última compra")
    meses_desde_ultima_compra: int = Field(..., ge=0, description="Meses desde última compra")
    updated_at: Optional[datetime] = Field(None, description="Fecha de última actualización")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "producto_id": "PROD123",
                "producto_nombre": "Acetaminofén 500mg",
                "categoria_producto": "Analgésicos",
                "frecuencia_compra": 8,
                "cantidad_total": 800,
                "cantidad_promedio": 100.0,
                "ultima_compra": "2024-09-15",
                "meses_desde_ultima_compra": 1
            }
        }


class DevolucionItem(BaseModel):
    """Item de devolución del cliente"""
    id: str = Field(..., description="ID de la devolución")
    cliente_id: str = Field(..., description="ID del cliente")
    compra_orden_id: Optional[str] = Field(None, description="ID de la orden original")
    producto_id: str = Field(..., description="ID del producto devuelto")
    producto_nombre: str = Field(..., description="Nombre del producto devuelto")
    cantidad_devuelta: int = Field(..., ge=1, description="Cantidad devuelta")
    motivo: str = Field(..., description="Motivo de la devolución")
    categoria_motivo: Optional[str] = Field(None, description="Categoría del motivo")
    fecha_devolucion: date = Field(..., description="Fecha de la devolución")
    estado: Optional[str] = Field(None, description="Estado de la devolución")
    created_at: Optional[datetime] = Field(None, description="Fecha de creación del registro")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "DEV001",
                "compra_orden_id": "ORD001",
                "producto_id": "PROD123",
                "producto_nombre": "Acetaminofén 500mg",
                "cantidad_devuelta": 10,
                "motivo": "Producto vencido",
                "categoria_motivo": "calidad",
                "fecha_devolucion": "2024-09-20",
                "estado": "procesada"
            }
        }


class EstadisticasClienteResponse(BaseModel):
    """Estadísticas resumidas del cliente"""
    cliente_id: str = Field(..., description="ID del cliente")
    total_compras: int = Field(..., ge=0, description="Total de compras realizadas")
    total_productos_unicos: int = Field(..., ge=0, description="Total de productos únicos comprados")
    total_devoluciones: int = Field(..., ge=0, description="Total de devoluciones realizadas")
    valor_total_compras: Decimal = Field(..., description="Valor total de todas las compras")
    promedio_orden: Decimal = Field(..., description="Valor promedio por orden")
    frecuencia_compra_mensual: Decimal = Field(..., ge=0, description="Frecuencia de compra mensual")
    tasa_devolucion: Decimal = Field(..., ge=0, le=100, description="Tasa de devolución en porcentaje")
    cliente_desde: Optional[date] = Field(None, description="Fecha de primera compra")
    ultima_compra: Optional[date] = Field(None, description="Fecha de última compra")
    updated_at: Optional[datetime] = Field(None, description="Fecha de última actualización")
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }
        json_schema_extra = {
            "example": {
                "total_compras": 25,
                "total_productos_unicos": 15,
                "total_devoluciones": 2,
                "valor_total_compras": 1250000.50,
                "promedio_orden": 50000.02,
                "frecuencia_compra_mensual": 2.1,
                "tasa_devolucion": 8.0,
                "cliente_desde": "2023-06-15",
                "ultima_compra": "2024-09-15"
            }
        }


class HistoricoCompletoResponse(BaseModel):
    """Respuesta completa del histórico del cliente"""
    cliente: ClienteBasicoResponse = Field(..., description="Información básica del cliente")
    historico_compras: List[CompraHistoricoItem] = Field(
        default=[], 
        description="Histórico de compras del cliente"
    )
    productos_preferidos: List[ProductoPreferidoItem] = Field(
        default=[], 
        description="Productos preferidos y frecuencia de compra"
    )
    devoluciones: List[DevolucionItem] = Field(
        default=[], 
        description="Devoluciones realizadas con motivos"
    )
    estadisticas: EstadisticasClienteResponse = Field(
        ..., 
        description="Estadísticas resumidas del cliente"
    )
    metadatos: Dict[str, Any] = Field(
        default={}, 
        description="Metadatos de la consulta (tiempo de respuesta, etc.)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "cliente": {
                    "id": "CLI001",
                    "nit": "900123456-7",
                    "nombre": "Farmacia San José",
                    "codigo_unico": "FSJ001",
                    "email": "contacto@farmaciasanjose.com",
                    "ciudad": "Bogotá",
                    "pais": "CO",
                    "activo": True
                },
                "historico_compras": [],
                "productos_preferidos": [],
                "devoluciones": [],
                "estadisticas": {
                    "total_compras": 25,
                    "total_productos_unicos": 15,
                    "total_devoluciones": 2
                },
                "metadatos": {
                    "consulta_took_ms": 850,
                    "fecha_consulta": "2024-10-11T10:30:00Z",
                    "limite_meses": 12,
                    "vendedor_id": "VEN001"
                }
            }
        }


# ==========================================
# ESQUEMAS DE AUDITORIA Y TRAZABILIDAD
# ==========================================

class ConsultaAuditoriaResponse(BaseModel):
    """Respuesta de registro de auditoría de consulta"""
    id: int = Field(..., description="ID del registro de auditoría")
    vendedor_id: str = Field(..., description="ID del vendedor")
    cliente_id: str = Field(..., description="ID del cliente consultado")
    tipo_consulta: str = Field(..., description="Tipo de consulta realizada")
    termino_busqueda: Optional[str] = Field(None, description="Término usado en la búsqueda")
    took_ms: int = Field(..., description="Tiempo de respuesta en milisegundos")
    timestamp: datetime = Field(..., description="Timestamp de la consulta")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 123,
                "vendedor_id": "VEN001",
                "cliente_id": "CLI001",
                "tipo_consulta": "busqueda_por_nit",
                "termino_busqueda": "900123456-7",
                "took_ms": 850,
                "timestamp": "2024-10-11T10:30:00Z"
            }
        }


# ==========================================
# ESQUEMAS DE ERROR Y VALIDACIÓN
# ==========================================

class ErrorResponse(BaseModel):
    """Esquema estándar de respuesta de error"""
    error: str = Field(..., description="Tipo de error")
    message: str = Field(..., description="Mensaje de error")
    details: Optional[Dict[str, Any]] = Field(None, description="Detalles adicionales del error")
    timestamp: Optional[str] = Field(None, description="Timestamp del error")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "CLIENT_NOT_FOUND",
                "message": "Cliente no encontrado con el término de búsqueda proporcionado",
                "details": {
                    "termino_busqueda": "900999999-9",
                    "sugerencias": ["Verificar el NIT", "Usar nombre completo", "Probar código único"]
                },
                "timestamp": "2024-10-11T10:30:00Z"
            }
        }


class ValidacionResponse(BaseModel):
    """Respuesta de validación de performance"""
    cumple_sla: bool = Field(..., description="Si cumple el SLA de ≤ 2 segundos")
    tiempo_respuesta_ms: int = Field(..., description="Tiempo de respuesta en milisegundos")
    limite_sla_ms: int = Field(default=2000, description="Límite SLA en milisegundos")
    advertencias: List[str] = Field(default=[], description="Advertencias de performance")
    
    class Config:
        json_schema_extra = {
            "example": {
                "cumple_sla": True,
                "tiempo_respuesta_ms": 850,
                "limite_sla_ms": 2000,
                "advertencias": []
            }
        }
