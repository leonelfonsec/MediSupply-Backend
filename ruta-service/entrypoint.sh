#!/bin/bash
set -e

echo "⏳ Esperando a que la base de datos esté lista..."
# Retry con Python (intenta conectar cada 1s)
python - <<'EOF'
import os, time
from sqlalchemy import create_engine
url = os.getenv("DATABASE_URL")
assert url, "DATABASE_URL no definida"
while True:
    try:
        create_engine(url).connect().close()
        break
    except Exception as e:
        print("DB no lista:", e)
        time.sleep(1)
print("✅ DB lista")
EOF

echo "🌱 Ejecutando seed si la tabla está vacía..."
python - <<'EOF'
from sqlmodel import Session, select
from database import engine
from models import Visita
from seed import visitas

with Session(engine) as session:
    existe = session.exec(select(Visita).limit(1)).first()
    if not existe:
        session.add_all(visitas)
        session.commit()
        print("✅ Datos iniciales cargados.")
    else:
        print("➡️  Datos ya existen. Seed omitido.")
EOF

echo "🚀 Iniciando FastAPI..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
