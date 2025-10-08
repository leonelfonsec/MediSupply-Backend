CREATE TABLE producto (
  id VARCHAR(64) PRIMARY KEY,
  codigo VARCHAR(64) UNIQUE NOT NULL,
  nombre VARCHAR(255) NOT NULL,
  categoria_id VARCHAR(64) NOT NULL,
  presentacion VARCHAR(128),
  precio_unitario NUMERIC(12,2) NOT NULL,
  requisitos_almacenamiento VARCHAR(128),
  activo BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE inventario (
  id BIGSERIAL PRIMARY KEY,
  producto_id VARCHAR(64) NOT NULL REFERENCES producto(id),
  pais CHAR(2) NOT NULL,
  bodega_id VARCHAR(64) NOT NULL,
  lote VARCHAR(64) NOT NULL,
  cantidad INT NOT NULL,
  vence DATE NOT NULL,
  condiciones VARCHAR(128)
);

CREATE INDEX idx_prod_codigo ON producto(codigo);
CREATE INDEX idx_prod_cat ON producto(categoria_id);
CREATE INDEX idx_inv_lookup ON inventario(producto_id, pais, bodega_id, lote);
CREATE INDEX idx_inv_vence  ON inventario(vence);

CREATE TABLE consulta_catalogo_log (
  id BIGSERIAL PRIMARY KEY,
  user_id VARCHAR(64),
  endpoint TEXT NOT NULL,
  filtros JSONB NOT NULL,
  took_ms INT NOT NULL,
  canal VARCHAR(16) NOT NULL DEFAULT 'mobile',
  ts TIMESTAMP NOT NULL DEFAULT now()
);
