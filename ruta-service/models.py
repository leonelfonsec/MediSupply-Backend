from sqlmodel import SQLModel, Field
from datetime import date

class Visita(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    vendedor_id: int
    cliente: str
    direccion: str
    fecha: date
    hora: str
    lat: float
    lng: float
