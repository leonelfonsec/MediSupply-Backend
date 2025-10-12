"""
Script para crear la base de datos del cliente-service
Orientado del catalogo-service para consistencia
"""
import os
import psycopg

host = os.getenv("PGHOST", "cliente-db")
user = os.getenv("POSTGRES_USER", "user")
password = os.getenv("POSTGRES_PASSWORD", "password")
target_db = os.getenv("TARGET_DB", "cliente")

admin_dsn = f"host={host} dbname=postgres user={user} password={password}"

print(f"🔄 Inicializando base de datos '{target_db}' en {host}...")

try:
    with psycopg.connect(admin_dsn) as conn:
        # fuera de transacción para CREATE DATABASE
        conn.autocommit = True
        with conn.cursor() as cur:
            # Verificar si la base de datos existe
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (target_db,))
            exists = cur.fetchone() is not None
            
            if not exists:
                cur.execute(f'CREATE DATABASE "{target_db}"')
                print(f"✅ Base de datos '{target_db}' creada exitosamente.")
            else:
                print(f"ℹ️  Base de datos '{target_db}' ya existe.")

    print(f"🎉 Inicialización de base de datos completada.")

except Exception as e:
    print(f"❌ Error al inicializar base de datos: {e}")
    raise