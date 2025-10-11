from pydantic import BaseModel
from typing import List, Optional

class InventarioResumen(BaseModel):
    cantidadTotal: int
    paises: List[str] = []

class Product(BaseModel):
    id: str
    nombre: str
    codigo: str
    categoria: str
    presentacion: Optional[str] = None
    precioUnitario: float
    requisitosAlmacenamiento: Optional[str] = None
    inventarioResumen: Optional[InventarioResumen] = None

class StockItem(BaseModel):
    pais: str
    bodegaId: str
    lote: str
    cantidad: int
    vence: str
    condiciones: str | None = None

class Meta(BaseModel):
    page: int
    size: int
    total: int
    tookMs: int

class SearchResponse(BaseModel):
    items: List[Product]
    meta: Meta
