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

-- ===================================================================
-- DATOS DE PRUEBA PARA DEMOSTRACIÓN
-- ===================================================================

-- Insertar productos de muestra (25 productos para probar paginación)
INSERT INTO producto (id, codigo, nombre, categoria_id, presentacion, precio_unitario, requisitos_almacenamiento, activo) VALUES
-- Antibióticos
('PROD001', 'AMX500', 'Amoxicilina 500mg', 'ANTIBIOTICS', 'Cápsula', 1250.00, 'Temperatura ambiente, lugar seco', TRUE),
('PROD002', 'CIP250', 'Ciprofloxacina 250mg', 'ANTIBIOTICS', 'Tableta', 850.00, 'Proteger de la luz', TRUE),
('PROD003', 'AZI500', 'Azitromicina 500mg', 'ANTIBIOTICS', 'Tableta recubierta', 2100.00, 'Temperatura ambiente', TRUE),
('PROD004', 'CLX500', 'Cloxacilina 500mg', 'ANTIBIOTICS', 'Cápsula', 980.00, 'Lugar seco, temperatura ambiente', TRUE),
('PROD005', 'CFX100', 'Cefalexina 100mg', 'ANTIBIOTICS', 'Suspensión', 1450.00, 'Refrigerar después de reconstituir', TRUE),

-- Analgésicos
('PROD006', 'IBU400', 'Ibuprofeno 400mg', 'ANALGESICS', 'Tableta', 320.00, 'Temperatura ambiente', TRUE),
('PROD007', 'ACE500', 'Acetaminofén 500mg', 'ANALGESICS', 'Tableta', 180.00, 'Lugar seco', TRUE),
('PROD008', 'ASP100', 'Aspirina 100mg', 'ANALGESICS', 'Tableta', 290.00, 'Proteger de la humedad', TRUE),
('PROD009', 'DIC50', 'Diclofenaco 50mg', 'ANALGESICS', 'Tableta recubierta', 450.00, 'Temperatura ambiente', TRUE),
('PROD010', 'NAP250', 'Naproxeno 250mg', 'ANALGESICS', 'Tableta', 380.00, 'Lugar seco', TRUE),

-- Cardiovasculares
('PROD011', 'ENL10', 'Enalapril 10mg', 'CARDIOVASCULAR', 'Tableta', 520.00, 'Temperatura ambiente', TRUE),
('PROD012', 'AML5', 'Amlodipino 5mg', 'CARDIOVASCULAR', 'Tableta', 420.00, 'Proteger de la luz', TRUE),
('PROD013', 'ATE50', 'Atenolol 50mg', 'CARDIOVASCULAR', 'Tableta', 350.00, 'Temperatura ambiente', TRUE),
('PROD014', 'LSN10', 'Losartán 10mg', 'CARDIOVASCULAR', 'Tableta recubierta', 680.00, 'Lugar seco', TRUE),
('PROD015', 'MET500', 'Metformina 500mg', 'CARDIOVASCULAR', 'Tableta', 280.00, 'Temperatura ambiente', TRUE),

-- Respiratorios
('PROD016', 'SAL100', 'Salbutamol 100mcg', 'RESPIRATORY', 'Inhalador', 1850.00, 'No exceder 30°C', TRUE),
('PROD017', 'LOR10', 'Loratadina 10mg', 'RESPIRATORY', 'Tableta', 320.00, 'Lugar seco', TRUE),
('PROD018', 'CET10', 'Cetirizina 10mg', 'RESPIRATORY', 'Tableta', 380.00, 'Temperatura ambiente', TRUE),
('PROD019', 'FEX120', 'Fexofenadina 120mg', 'RESPIRATORY', 'Tableta', 450.00, 'Proteger de la humedad', TRUE),
('PROD020', 'BUD200', 'Budesonida 200mcg', 'RESPIRATORY', 'Inhalador', 2100.00, 'Refrigerar', TRUE),

-- Gastrointestinales
('PROD021', 'OME20', 'Omeprazol 20mg', 'GASTROINTESTINAL', 'Cápsula', 480.00, 'Proteger de la humedad', TRUE),
('PROD022', 'RAN150', 'Ranitidina 150mg', 'GASTROINTESTINAL', 'Tableta', 320.00, 'Temperatura ambiente', TRUE),
('PROD023', 'DOM10', 'Domperidona 10mg', 'GASTROINTESTINAL', 'Tableta', 290.00, 'Lugar seco', TRUE),
('PROD024', 'LOP2', 'Loperamida 2mg', 'GASTROINTESTINAL', 'Cápsula', 380.00, 'Temperatura ambiente', TRUE),
('PROD025', 'SMT40', 'Simeticona 40mg', 'GASTROINTESTINAL', 'Tableta masticable', 250.00, 'Lugar seco', TRUE);

-- Insertar inventario para los productos (múltiples países y bodegas para probar filtros)
INSERT INTO inventario (producto_id, pais, bodega_id, lote, cantidad, vence, condiciones) VALUES
-- Amoxicilina en varias ubicaciones
('PROD001', 'CO', 'BOG_CENTRAL', 'AMX001_2024', 500, '2025-12-31', 'Almacén principal'),
('PROD001', 'CO', 'MED_SUR', 'AMX002_2024', 300, '2025-11-30', 'Bodega refrigerada'),
('PROD001', 'MX', 'CDMX_NORTE', 'AMX003_2024', 750, '2026-01-15', 'Centro de distribución'),
('PROD001', 'PE', 'LIM_CALLAO', 'AMX004_2024', 200, '2025-10-31', 'Almacén secundario'),

-- Ciprofloxacina
('PROD002', 'CO', 'BOG_CENTRAL', 'CIP001_2024', 400, '2025-09-30', 'Área protegida de luz'),
('PROD002', 'MX', 'GDL_OESTE', 'CIP002_2024', 600, '2025-08-31', 'Bodega climatizada'),
('PROD002', 'CL', 'SCL_CENTRO', 'CIP003_2024', 350, '2026-02-28', 'Almacén principal'),

-- Ibuprofeno (popular, muchas existencias)
('PROD006', 'CO', 'BOG_CENTRAL', 'IBU001_2024', 1000, '2026-06-30', 'Almacén general'),
('PROD006', 'CO', 'MED_SUR', 'IBU002_2024', 800, '2026-05-31', 'Bodega principal'),
('PROD006', 'MX', 'CDMX_NORTE', 'IBU003_2024', 1200, '2026-07-31', 'Centro de distribución'),
('PROD006', 'PE', 'LIM_CALLAO', 'IBU004_2024', 600, '2026-04-30', 'Almacén secundario'),
('PROD006', 'CL', 'SCL_CENTRO', 'IBU005_2024', 900, '2026-08-31', 'Bodega central'),

-- Acetaminofén (muy popular)
('PROD007', 'CO', 'BOG_CENTRAL', 'ACE001_2024', 1500, '2025-12-31', 'Almacén general'),
('PROD007', 'MX', 'CDMX_NORTE', 'ACE002_2024', 2000, '2026-01-31', 'Centro principal'),
('PROD007', 'PE', 'LIM_CALLAO', 'ACE003_2024', 800, '2025-11-30', 'Bodega local'),

-- Enalapril cardiovascular
('PROD011', 'CO', 'BOG_CENTRAL', 'ENL001_2024', 300, '2025-10-31', 'Medicamentos especiales'),
('PROD011', 'MX', 'GDL_OESTE', 'ENL002_2024', 250, '2025-09-30', 'Área cardiovascular'),
('PROD011', 'CL', 'SCL_CENTRO', 'ENL003_2024', 400, '2026-03-31', 'Bodega especializada'),

-- Salbutamol respiratorio (requiere refrigeración)
('PROD016', 'CO', 'BOG_CENTRAL', 'SAL001_2024', 150, '2025-08-31', 'Refrigeración controlada'),
('PROD016', 'MX', 'CDMX_NORTE', 'SAL002_2024', 200, '2025-07-31', 'Cámara fría'),
('PROD016', 'PE', 'LIM_CALLAO', 'SAL003_2024', 100, '2025-06-30', 'Almacén refrigerado'),

-- Omeprazol gastrointestinal
('PROD021', 'CO', 'BOG_CENTRAL', 'OME001_2024', 600, '2025-12-31', 'Zona seca'),
('PROD021', 'MX', 'GDL_OESTE', 'OME002_2024', 450, '2025-11-30', 'Almacén principal'),
('PROD021', 'CL', 'SCL_CENTRO', 'OME003_2024', 500, '2026-01-31', 'Bodega climatizada'),

-- Agregar inventario para más productos para tener datos suficientes
('PROD003', 'CO', 'BOG_CENTRAL', 'AZI001_2024', 200, '2025-09-30', 'Almacén antibióticos'),
('PROD008', 'CO', 'MED_SUR', 'ASP001_2024', 800, '2026-03-31', 'Bodega general'),
('PROD012', 'MX', 'CDMX_NORTE', 'AML001_2024', 350, '2025-10-31', 'Área cardiovascular'),
('PROD017', 'PE', 'LIM_CALLAO', 'LOR001_2024', 600, '2026-02-28', 'Medicamentos respiratorios'),
('PROD022', 'CL', 'SCL_CENTRO', 'RAN001_2024', 400, '2025-11-30', 'Zona gastrointestinal');
