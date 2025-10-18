-- Inicialización de base de datos para cliente-service
-- HU07: Consultar Cliente - Estructura y datos iniciales

-- ====================================================
-- CREACIÓN DE TABLAS
-- ====================================================

-- Tabla principal de clientes
CREATE TABLE IF NOT EXISTS cliente (
    id VARCHAR(64) PRIMARY KEY,
    nit VARCHAR(20) UNIQUE NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    codigo_unico VARCHAR(64) UNIQUE NOT NULL,
    email VARCHAR(255),
    telefono VARCHAR(50),
    direccion TEXT,
    ciudad VARCHAR(100),
    pais CHAR(2) DEFAULT 'CO',
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de histórico de compras
CREATE TABLE IF NOT EXISTS compra_historico (
    id VARCHAR(64) PRIMARY KEY,
    cliente_id VARCHAR(64) NOT NULL REFERENCES cliente(id),
    orden_id VARCHAR(64) NOT NULL,
    estado_orden VARCHAR(50) DEFAULT 'completada',
    producto_id VARCHAR(64) NOT NULL,
    producto_nombre VARCHAR(255) NOT NULL,
    categoria_producto VARCHAR(100),
    cantidad INTEGER NOT NULL,
    precio_unitario DECIMAL(12,2) NOT NULL,
    precio_total DECIMAL(12,2) NOT NULL,
    fecha_compra DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de devoluciones
CREATE TABLE IF NOT EXISTS devolucion_historico (
    id VARCHAR(64) PRIMARY KEY,
    cliente_id VARCHAR(64) NOT NULL REFERENCES cliente(id),
    compra_id VARCHAR(64),
    compra_orden_id VARCHAR(64),
    producto_id VARCHAR(64) NOT NULL,
    producto_nombre VARCHAR(255) NOT NULL,
    cantidad_devuelta INTEGER NOT NULL,
    motivo TEXT NOT NULL,
    categoria_motivo VARCHAR(100),
    estado VARCHAR(50) DEFAULT 'procesada',
    fecha_devolucion DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de log de consultas (trazabilidad)
CREATE TABLE IF NOT EXISTS consulta_cliente_log (
    id BIGSERIAL PRIMARY KEY,
    vendedor_id VARCHAR(64) NOT NULL,
    cliente_id VARCHAR(64),
    tipo_consulta VARCHAR(100) NOT NULL,
    tipo_busqueda VARCHAR(50),
    termino_busqueda VARCHAR(255),
    took_ms INTEGER,
    metadatos JSONB,
    fecha_consulta TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de productos preferidos (calculada)
CREATE TABLE IF NOT EXISTS producto_preferido (
    id BIGSERIAL PRIMARY KEY,
    cliente_id VARCHAR(64) NOT NULL REFERENCES cliente(id),
    producto_id VARCHAR(64) NOT NULL,
    producto_nombre VARCHAR(255) NOT NULL,
    categoria_producto VARCHAR(100),
    frecuencia_compra INTEGER DEFAULT 1,
    cantidad_total INTEGER DEFAULT 0,
    cantidad_promedio DECIMAL(8,2) DEFAULT 0,
    ultima_compra DATE,
    meses_desde_ultima INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de estadísticas de cliente
CREATE TABLE IF NOT EXISTS estadistica_cliente (
    id BIGSERIAL PRIMARY KEY,
    cliente_id VARCHAR(64) NOT NULL REFERENCES cliente(id),
    total_compras INTEGER DEFAULT 0,
    total_productos_unicos INTEGER DEFAULT 0,
    total_devoluciones INTEGER DEFAULT 0,
    valor_total_compras DECIMAL(15,2) DEFAULT 0,
    promedio_orden DECIMAL(12,2) DEFAULT 0,
    frecuencia_compra_mensual DECIMAL(8,2) DEFAULT 0,
    tasa_devolucion DECIMAL(5,2) DEFAULT 0,
    cliente_desde DATE,
    ultima_compra DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_cliente_nit ON cliente(nit);
CREATE INDEX IF NOT EXISTS idx_cliente_codigo ON cliente(codigo_unico);
CREATE INDEX IF NOT EXISTS idx_cliente_nombre ON cliente(nombre);
CREATE INDEX IF NOT EXISTS idx_compra_cliente ON compra_historico(cliente_id);
CREATE INDEX IF NOT EXISTS idx_compra_fecha ON compra_historico(fecha_compra);
CREATE INDEX IF NOT EXISTS idx_compra_producto ON compra_historico(producto_id);
CREATE INDEX IF NOT EXISTS idx_devolucion_cliente ON devolucion_historico(cliente_id);
CREATE INDEX IF NOT EXISTS idx_devolucion_fecha ON devolucion_historico(fecha_devolucion);
CREATE INDEX IF NOT EXISTS idx_consulta_vendedor ON consulta_cliente_log(vendedor_id);
CREATE INDEX IF NOT EXISTS idx_consulta_cliente ON consulta_cliente_log(cliente_id);
CREATE INDEX IF NOT EXISTS idx_consulta_fecha ON consulta_cliente_log(fecha_consulta);

-- ====================================================
-- DATOS DE CLIENTES DE EJEMPLO
-- ====================================================

INSERT INTO cliente (id, nit, nombre, codigo_unico, email, telefono, direccion, ciudad, pais, activo, created_at) VALUES
('CLI001', '900123456-7', 'Farmacia San José', 'FSJ001', 'contacto@farmaciasanjose.com', '+57-1-2345678', 'Calle 45 #12-34', 'Bogotá', 'CO', true, NOW()),
('CLI002', '800987654-3', 'Droguería El Buen Pastor', 'DBP002', 'ventas@elbunpastor.com', '+57-2-9876543', 'Carrera 15 #67-89', 'Medellín', 'CO', true, NOW()),
('CLI003', '700456789-1', 'Farmatodo Zona Norte', 'FZN003', 'info@farmatodo.com', '+57-5-4567890', 'Avenida Norte #23-45', 'Barranquilla', 'CO', true, NOW()),
('CLI004', '600345678-9', 'Centro Médico Salud Total', 'CST004', 'compras@saludtotal.com', '+57-1-3456789', 'Calle 85 #34-56', 'Bogotá', 'CO', true, NOW()),
('CLI005', '500234567-5', 'Farmacia Popular', 'FPO005', 'pedidos@farmapopular.com', '+57-4-2345678', 'Carrera 70 #45-67', 'Medellín', 'CO', true, NOW());

-- ====================================================
-- HISTÓRICO DE COMPRAS DE EJEMPLO
-- ====================================================

INSERT INTO compra_historico (id, cliente_id, orden_id, estado_orden, producto_id, producto_nombre, categoria_producto, cantidad, precio_unitario, precio_total, fecha_compra, created_at) VALUES
-- Cliente CLI001 - Farmacia San José (comprador frecuente)
('COMP001', 'CLI001', 'ORD2024001', 'completada', 'ACETA500', 'Acetaminofén 500mg x 20 tabletas', 'Analgésicos', 50, 1200.00, 60000.00, '2024-09-15', NOW()),
('COMP002', 'CLI001', 'ORD2024002', 'completada', 'IBUPRO400', 'Ibuprofeno 400mg x 20 cápsulas', 'Antiinflamatorios', 30, 1800.00, 54000.00, '2024-09-10', NOW()),
('COMP003', 'CLI001', 'ORD2024003', 'completada', 'ACETA500', 'Acetaminofén 500mg x 20 tabletas', 'Analgésicos', 75, 1200.00, 90000.00, '2024-08-20', NOW()),
('COMP004', 'CLI001', 'ORD2024004', 'completada', 'OMEPRA20', 'Omeprazol 20mg x 14 cápsulas', 'Gastroprotectores', 20, 3500.00, 70000.00, '2024-08-15', NOW()),
('COMP005', 'CLI001', 'ORD2024005', 'completada', 'ACETA500', 'Acetaminofén 500mg x 20 tabletas', 'Analgésicos', 100, 1200.00, 120000.00, '2024-07-30', NOW()),
('COMP006', 'CLI001', 'ORD2024006', 'completada', 'LORATA10', 'Loratadina 10mg x 10 tabletas', 'Antihistamínicos', 25, 800.00, 20000.00, '2024-07-15', NOW()),

-- Cliente CLI002 - Droguería El Buen Pastor
('COMP007', 'CLI002', 'ORD2024007', 'completada', 'IBUPRO400', 'Ibuprofeno 400mg x 20 cápsulas', 'Antiinflamatorios', 40, 1800.00, 72000.00, '2024-09-12', NOW()),
('COMP008', 'CLI002', 'ORD2024008', 'completada', 'DIPIRO500', 'Dipirona 500mg x 20 tabletas', 'Analgésicos', 60, 900.00, 54000.00, '2024-09-05', NOW()),
('COMP009', 'CLI002', 'ORD2024009', 'completada', 'AMOXIC500', 'Amoxicilina 500mg x 21 cápsulas', 'Antibióticos', 15, 4200.00, 63000.00, '2024-08-25', NOW()),

-- Cliente CLI003 - Farmatodo Zona Norte
('COMP010', 'CLI003', 'ORD2024010', 'completada', 'ACETA500', 'Acetaminofén 500mg x 20 tabletas', 'Analgésicos', 80, 1200.00, 96000.00, '2024-09-08', NOW()),
('COMP011', 'CLI003', 'ORD2024011', 'completada', 'VITAMI500', 'Complejo B x 30 tabletas', 'Vitaminas', 35, 2500.00, 87500.00, '2024-08-30', NOW()),

-- Cliente CLI004 - Centro Médico Salud Total
('COMP012', 'CLI004', 'ORD2024012', 'completada', 'OMEPRA20', 'Omeprazol 20mg x 14 cápsulas', 'Gastroprotectores', 50, 3500.00, 175000.00, '2024-09-01', NOW()),
('COMP013', 'CLI004', 'ORD2024013', 'completada', 'LOSART50', 'Losartán 50mg x 30 tabletas', 'Antihipertensivos', 25, 2800.00, 70000.00, '2024-08-18', NOW()),

-- Cliente CLI005 - Farmacia Popular
('COMP014', 'CLI005', 'ORD2024014', 'completada', 'ACETA500', 'Acetaminofén 500mg x 20 tabletas', 'Analgésicos', 40, 1200.00, 48000.00, '2024-08-10', NOW()),
('COMP015', 'CLI005', 'ORD2024015', 'completada', 'DIPIRO500', 'Dipirona 500mg x 20 tabletas', 'Analgésicos', 30, 900.00, 27000.00, '2024-07-25', NOW());

-- ====================================================
-- DEVOLUCIONES DE EJEMPLO
-- ====================================================

INSERT INTO devolucion_historico (id, cliente_id, compra_id, compra_orden_id, producto_id, producto_nombre, cantidad_devuelta, motivo, categoria_motivo, estado, fecha_devolucion, created_at) VALUES
-- Devoluciones de CLI001
('DEV001', 'CLI001', 'COMP002', 'ORD2024002', 'IBUPRO400', 'Ibuprofeno 400mg x 20 cápsulas', 5, 'Producto próximo a vencer - fecha de vencimiento muy cercana', 'vencimiento', 'procesada', '2024-09-18', NOW()),
('DEV002', 'CLI001', 'COMP004', 'ORD2024004', 'OMEPRA20', 'Omeprazol 20mg x 14 cápsulas', 3, 'Cápsulas con defecto en el blister - empaque dañado', 'calidad', 'procesada', '2024-08-22', NOW()),

-- Devoluciones de CLI002
('DEV003', 'CLI002', 'COMP009', 'ORD2024009', 'AMOXIC500', 'Amoxicilina 500mg x 21 cápsulas', 2, 'Error en el pedido - cliente solicitó presentación de 250mg', 'error_pedido', 'procesada', '2024-08-28', NOW()),

-- Devoluciones de CLI003
('DEV004', 'CLI003', 'COMP010', 'ORD2024010', 'ACETA500', 'Acetaminofén 500mg x 20 tabletas', 8, 'Producto vencido al momento de la entrega', 'vencimiento', 'procesada', '2024-09-12', NOW());

-- ====================================================
-- LOGS DE CONSULTA DE EJEMPLO (para trazabilidad)
-- ====================================================

INSERT INTO consulta_cliente_log (vendedor_id, cliente_id, tipo_consulta, tipo_busqueda, termino_busqueda, took_ms, metadatos, fecha_consulta) VALUES
-- Consultas del vendedor VEN001
('VEN001', 'CLI001', 'busqueda_cliente', 'nit', '900123456-7', 850, '{"resultado_encontrado": true, "cliente_nombre": "Farmacia San José"}', '2024-10-10 10:30:00'),
('VEN001', 'CLI001', 'historico_completo', null, null, 1200, '{"limite_meses": 12, "total_compras": 6, "total_devoluciones": 2}', '2024-10-10 10:31:00'),
('VEN001', 'CLI002', 'busqueda_cliente', 'nombre', 'Droguería El Buen Pastor', 650, '{"resultado_encontrado": true, "cliente_nit": "800987654-3"}', '2024-10-10 11:15:00'),

-- Consultas del vendedor VEN002
('VEN002', 'CLI003', 'busqueda_cliente', 'codigo', 'FZN003', 400, '{"resultado_encontrado": true, "cliente_nombre": "Farmatodo Zona Norte"}', '2024-10-10 14:20:00'),
('VEN002', 'CLI003', 'historico_completo', null, null, 980, '{"limite_meses": 6, "total_compras": 2, "total_devoluciones": 1}', '2024-10-10 14:21:00');

-- ====================================================
-- COMENTARIOS EXPLICATIVOS
-- ====================================================

-- Este script de datos de ejemplo incluye:
--
-- 1. CLIENTES DIVERSOS:
--    - Farmacias independientes
--    - Cadenas de droguerías  
--    - Centros médicos
--    - Diferentes ciudades de Colombia
--
-- 2. HISTÓRICO DE COMPRAS REALISTA:
--    - Productos farmacéuticos comunes
--    - Diferentes categorías (analgésicos, antibióticos, etc.)
--    - Cantidades y precios realistas
--    - Fechas distribuidas en los últimos meses
--    - Productos preferidos (Acetaminofén aparece frecuentemente)
--
-- 3. DEVOLUCIONES CON MOTIVOS REALES:
--    - Productos vencidos
--    - Defectos de calidad
--    - Errores en pedidos
--    - Categorías de motivos para análisis
--
-- 4. TRAZABILIDAD DE CONSULTAS:
--    - Logs de diferentes vendedores
--    - Diferentes tipos de búsqueda (NIT, nombre, código)
--    - Métricas de performance (tiempo de respuesta)
--    - Cumplimiento de SLA
--
-- Estos datos permiten probar todos los criterios de aceptación:
-- ✅ Búsqueda por NIT, nombre o código único
-- ✅ Histórico de compras con productos, cantidades, fechas  
-- ✅ Productos preferidos y frecuencia de compra
-- ✅ Devoluciones con motivos
-- ✅ Performance ≤ 2 segundos (datos en logs)
-- ✅ Trazabilidad registrada