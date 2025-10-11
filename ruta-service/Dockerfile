FROM python:3.11-slim

# Crear directorio
WORKDIR /app

# Copiar archivos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Exponer el puerto
EXPOSE 8000

# Comando por defecto
CMD ["bash", "-c", "python seed.py && uvicorn main:app --host 0.0.0.0 --port 8000"]


