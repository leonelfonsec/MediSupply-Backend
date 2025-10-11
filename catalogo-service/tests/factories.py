import factory
from faker import Faker
from datetime import datetime, timedelta
import random
import string
from app.models.catalogo_model import Producto, Inventario

fake = Faker(['es_ES', 'en_US'])  # Español e inglés para datos realistas

class ProductoFactory(factory.Factory):
    """Factory para generar productos usando Faker."""
    
    class Meta:
        model = Producto

    id = factory.LazyFunction(lambda: f"PROD{fake.random_int(min=1000, max=9999)}")
    codigo = factory.LazyFunction(lambda: f"{fake.lexify(text='???').upper()}{fake.random_int(min=100, max=999)}")
    nombre = factory.LazyFunction(lambda: fake.random_element(elements=[
        f"{fake.random_element(['Amoxicilina', 'Ciprofloxacina', 'Azitromicina', 'Ibuprofeno', 'Acetaminofén', 'Diclofenaco'])} {fake.random_element(['500mg', '250mg', '100mg', '50mg'])}",
        f"{fake.random_element(['Enalapril', 'Amlodipino', 'Losartán', 'Atenolol'])} {fake.random_element(['5mg', '10mg', '25mg', '50mg'])}",
        f"{fake.random_element(['Omeprazol', 'Ranitidina', 'Domperidona'])} {fake.random_element(['20mg', '150mg', '10mg'])}",
        f"{fake.random_element(['Salbutamol', 'Loratadina', 'Cetirizina'])} {fake.random_element(['100mcg', '10mg', '5mg'])}"
    ]))
    categoria_id = factory.LazyFunction(lambda: fake.random_element([
        'ANTIBIOTICS', 'ANALGESICS', 'CARDIOVASCULAR', 
        'RESPIRATORY', 'GASTROINTESTINAL', 'DERMATOLOGY'
    ]))
    presentacion = factory.LazyFunction(lambda: fake.random_element([
        'Tableta', 'Cápsula', 'Jarabe', 'Suspensión', 'Inhalador', 
        'Crema', 'Solución inyectable', 'Tableta recubierta'
    ]))
    precio_unitario = factory.LazyFunction(lambda: round(fake.random_int(min=100, max=5000) / 100, 2))
    requisitos_almacenamiento = factory.LazyFunction(lambda: fake.random_element([
        'Temperatura ambiente', 'Refrigerar entre 2-8°C', 'Proteger de la luz',
        'Lugar seco', 'No exceder 25°C', 'Proteger de la humedad',
        'Almacenar en lugar fresco y seco', 'Refrigerar después de reconstituir'
    ]))
    activo = True

class InventarioFactory(factory.Factory):
    """Factory para generar inventario usando Faker."""
    
    class Meta:
        model = Inventario

    id = factory.Sequence(lambda n: n)
    producto_id = factory.LazyFunction(lambda: f"PROD{fake.random_int(min=1000, max=9999)}")
    pais = factory.LazyFunction(lambda: fake.random_element(['CO', 'MX', 'PE', 'CL', 'AR', 'EC']))
    bodega_id = factory.LazyFunction(lambda: f"{fake.random_element(['BOG', 'MED', 'CDMX', 'GDL', 'LIM', 'SCL'])}_{fake.random_element(['CENTRAL', 'SUR', 'NORTE', 'OESTE'])}")
    lote = factory.LazyFunction(lambda: f"{fake.lexify(text='???').upper()}{fake.random_int(min=100, max=999)}_{fake.year()}")
    cantidad = factory.LazyFunction(lambda: fake.random_int(min=50, max=2000))
    vence = factory.LazyFunction(lambda: fake.date_between(start_date='today', end_date='+2y'))
    condiciones = factory.LazyFunction(lambda: fake.random_element([
        'Almacén principal', 'Bodega refrigerada', 'Centro de distribución',
        'Almacén secundario', 'Zona climatizada', 'Área protegida de luz',
        'Bodega especializada', 'Cámara fría'
    ]))

def generate_test_productos(count: int = 10):
    """Genera una lista de productos para pruebas."""
    return [ProductoFactory() for _ in range(count)]

def generate_test_inventario(producto_ids: list, count_per_product: int = 3):
    """Genera inventario para productos específicos."""
    inventarios = []
    for producto_id in producto_ids:
        for _ in range(count_per_product):
            inventario = InventarioFactory()
            inventario.producto_id = producto_id
            inventarios.append(inventario)
    return inventarios

def generate_search_scenarios():
    """Genera escenarios de búsqueda realistas para pruebas."""
    return [
        {"q": "amoxicilina", "expected_partial": True},
        {"q": "500mg", "expected_partial": True}, 
        {"categoriaId": "ANTIBIOTICS", "expected_category": True},
        {"categoriaId": "ANALGESICS", "expected_category": True},
        {"codigo": "AMX500", "expected_exact": True},
        {"pais": "CO", "expected_country": True},
        {"bodegaId": "BOG_CENTRAL", "expected_warehouse": True},
        {"q": "inexistente", "expected_empty": True}
    ]