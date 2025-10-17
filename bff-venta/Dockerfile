FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
ENV PYTHONUNBUFFERED=1

# Gunicorn en producción; para desarrollo puedes usar flask run
CMD ["gunicorn","wsgi:app","--bind", "0.0.0.0:8000","--workers", "2","--threads", "4","--access-logfile", "-","--error-logfile", "-","--log-level", "info","--capture-output"]