### Comandos rápidos

# 1) Crear entorno e instalar
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2) Configurar env
cp .env.example .env
# edita SQS_QUEUE_URL y otros valores

# 3) Ejecutar
python wsgi.py
# o
gunicorn -b 0.0.0.0:8000 wsgi:app

# 4) Docker
docker compose up --build
