from fastapi import FastAPI, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from database import get_session, init_db
from models import Visita
from datetime import date

app = FastAPI(title="Ruta Service")

# Configuración CORS para React Native
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica los dominios exactos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/api/ruta")
def obtener_ruta(
    fecha: date = Query(...),
    vendedor_id: int = Query(...),
    session: Session = Depends(get_session)
):
    query = select(Visita).where(Visita.fecha == fecha, Visita.vendedor_id == vendedor_id)
    visitas = session.exec(query).all()

    visitas_ordenadas = sorted(visitas, key=lambda v: v.hora)
    result = []
    for i, v in enumerate(visitas_ordenadas):
        data = v.dict()
        data["tiempo_desde_anterior"] = None if i == 0 else "15 min"  # Simulado
        result.append(data)

    return {"fecha": fecha, "visitas": result}
