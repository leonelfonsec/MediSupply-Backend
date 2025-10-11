# -------- Base común --------
FROM python:3.11-slim-bookworm AS base
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_ROOT_USER_ACTION=ignore \
    PYTHONHASHSEED=0

WORKDIR /app

# (A) Sistema mínimo: certificados
# Si tu prioridad es reducir CVEs, deja también 'apt-get upgrade'.
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Usuario no root
RUN groupadd -r appuser && useradd -r -m -g appuser appuser

# Instala runtime
COPY requirements.txt .
RUN python -m pip install --upgrade pip setuptools wheel \
 && pip install --no-cache-dir -r requirements.txt

# Copiamos código ya con ownership correcto
COPY --chown=appuser:appuser . .

# -------- Desarrollo: Uvicorn con reload --------
FROM base AS dev
ENV ENVIRONMENT=development \
    LOG_LEVEL=debug \
    PORT=3000
EXPOSE 3000
USER appuser
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3000", "--reload", "--log-level", "debug"]

# -------- Producción: Gunicorn + workers Uvicorn --------
FROM base AS prod
RUN pip install --no-cache-dir gunicorn
ENV ENVIRONMENT=production \
    LOG_LEVEL=info \
    WORKERS=2 \
    PORT=3000
EXPOSE 3000
USER appuser
CMD ["bash", "-lc", "gunicorn -k uvicorn.workers.UvicornWorker -w ${WORKERS:-2} -b 0.0.0.0:${PORT} app.main:app --access-logfile - --error-logfile -"]
