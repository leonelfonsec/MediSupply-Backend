import os
import psycopg

host = os.getenv("PGHOST", "catalog-db")
user = os.getenv("POSTGRES_USER", "user")
password = os.getenv("POSTGRES_PASSWORD", "password")
target_db = os.getenv("TARGET_DB", "catalogo")

admin_dsn = f"host={host} dbname=postgres user={user} password={password}"

with psycopg.connect(admin_dsn) as conn:
    # fuera de transacción para CREATE DATABASE
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (target_db,))
        exists = cur.fetchone() is not None
        if not exists:
            cur.execute(f'CREATE DATABASE "{target_db}"')
            print(f"Database {target_db} creada.")
        else:
            print(f"Database {target_db} ya existe.")