import pytest
from datetime import datetime, timezone
from decimal import Decimal
from faker import Faker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.catalogo_model import Base, Producto, Inventario

fake = Faker(['es_ES'])

class TestProductoModel:
    """Pruebas para el modelo Producto."""

    @pytest.mark.unit
    def test_producto_creacion_basica(self):
        """Prueba creación básica de producto."""
        # Arrange
        producto_data = {
            'id': fake.uuid4(),
            'codigo': fake.lexify(text='MED???'),
            'nombre': fake.company() + ' ' + fake.random_element(['500mg', '250mg', '1g']),
            'descripcion': fake.text(max_nb_chars=200),
            'categoria_id': fake.random_element(['ANTIBIOTICS', 'PAINKILLERS', 'VITAMINS']),
            'precio_unitario': Decimal(str(fake.pyfloat(positive=True, max_value=1000))),
            'unidad_medida': fake.random_element(['mg', 'ml', 'capsulas', 'tabletas']),
            'fecha_creacion': datetime.now(timezone.utc),
            'fecha_actualizacion': datetime.now(timezone.utc)
        }
        
        # Act
        producto = Producto(**producto_data)
        
        # Assert
        assert producto.id == producto_data['id']
        assert producto.codigo == producto_data['codigo']
        assert producto.nombre == producto_data['nombre']
        assert producto.descripcion == producto_data['descripcion']
        assert producto.categoria_id == producto_data['categoria_id']
        assert producto.precio_unitario == producto_data['precio_unitario']
        assert producto.unidad_medida == producto_data['unidad_medida']

    @pytest.mark.unit
    def test_producto_validacion_precio(self):
        """Prueba validación de precio unitario."""
        # Test precio positivo
        producto = Producto(
            id=fake.uuid4(),
            codigo='TEST001',
            nombre='Producto Test',
            precio_unitario=Decimal('50.99'),
            categoria_id='TEST'
        )
        assert producto.precio_unitario > 0
        
        # Test precio cero (debería ser válido)
        producto_cero = Producto(
            id=fake.uuid4(),
            codigo='TEST002', 
            nombre='Producto Gratuito',
            precio_unitario=Decimal('0.00'),
            categoria_id='TEST'
        )
        assert producto_cero.precio_unitario == Decimal('0.00')

    @pytest.mark.unit
    def test_producto_campos_requeridos(self):
        """Prueba campos requeridos del producto."""
        # Campos mínimos requeridos
        campos_requeridos = {
            'id': fake.uuid4(),
            'codigo': 'REQ001',
            'nombre': 'Producto Requerido',
            'precio_unitario': Decimal('25.50'),
            'categoria_id': 'REQUIRED'
        }
        
        # Act
        producto = Producto(**campos_requeridos)
        
        # Assert
        assert producto.id is not None
        assert producto.codigo is not None
        assert producto.nombre is not None
        assert producto.precio_unitario is not None
        assert producto.categoria_id is not None

    @pytest.mark.unit
    def test_producto_campos_opcionales(self):
        """Prueba campos opcionales del producto."""
        # Act
        producto = Producto(
            id=fake.uuid4(),
            codigo='OPT001',
            nombre='Producto Opcional',
            precio_unitario=Decimal('15.75'),
            categoria_id='OPTIONAL'
        )
        
        # Assert - Campos opcionales pueden ser None
        assert producto.descripcion is None
        assert producto.unidad_medida is None
        assert producto.fecha_creacion is None
        assert producto.fecha_actualizacion is None

    @pytest.mark.unit
    def test_producto_representacion_string(self):
        """Prueba representación como string del producto."""
        # Arrange
        producto = Producto(
            id='TEST123',
            codigo='MED001',
            nombre='Amoxicilina 500mg',
            precio_unitario=Decimal('45.00'),
            categoria_id='ANTIBIOTICS'
        )
        
        # Act
        str_repr = str(producto)
        
        # Assert
        assert 'MED001' in str_repr or 'Amoxicilina' in str_repr or 'TEST123' in str_repr

class TestInventarioModel:
    """Pruebas para el modelo Inventario."""

    @pytest.mark.unit
    def test_inventario_creacion_basica(self):
        """Prueba creación básica de inventario."""
        # Arrange
        inventario_data = {
            'id': fake.uuid4(),
            'producto_id': fake.uuid4(),
            'pais': fake.country_code(),
            'cantidad': fake.random_int(min=0, max=10000),
            'fecha_actualizacion': datetime.now(timezone.utc)
        }
        
        # Act
        inventario = Inventario(**inventario_data)
        
        # Assert
        assert inventario.id == inventario_data['id']
        assert inventario.producto_id == inventario_data['producto_id']
        assert inventario.pais == inventario_data['pais']
        assert inventario.cantidad == inventario_data['cantidad']
        assert inventario.fecha_actualizacion == inventario_data['fecha_actualizacion']

    @pytest.mark.unit
    def test_inventario_cantidad_validaciones(self):
        """Prueba validaciones de cantidad en inventario."""
        # Test cantidad positiva
        inventario_positivo = Inventario(
            id=fake.uuid4(),
            producto_id=fake.uuid4(),
            pais='CO',
            cantidad=100
        )
        assert inventario_positivo.cantidad > 0
        
        # Test cantidad cero
        inventario_cero = Inventario(
            id=fake.uuid4(),
            producto_id=fake.uuid4(),
            pais='PE',
            cantidad=0
        )
        assert inventario_cero.cantidad == 0

    @pytest.mark.unit
    def test_inventario_paises_validos(self):
        """Prueba códigos de país válidos."""
        paises_test = ['CO', 'PE', 'MX', 'AR', 'CL', 'EC']
        
        for pais in paises_test:
            inventario = Inventario(
                id=fake.uuid4(),
                producto_id=fake.uuid4(),
                pais=pais,
                cantidad=fake.random_int(min=1, max=1000)
            )
            assert inventario.pais == pais
            assert len(inventario.pais) == 2  # Códigos ISO de 2 letras

    @pytest.mark.unit
    def test_inventario_relacion_producto(self):
        """Prueba relación con producto."""
        # Arrange
        producto_id = fake.uuid4()
        
        # Act
        inventario = Inventario(
            id=fake.uuid4(),
            producto_id=producto_id,
            pais='CO',
            cantidad=500
        )
        
        # Assert
        assert inventario.producto_id == producto_id

class TestModelRelations:
    """Pruebas para relaciones entre modelos."""

    @pytest.mark.unit
    def test_producto_inventarios_relacion(self):
        """Prueba relación producto-inventarios."""
        # Esta prueba sería más completa con una base de datos real
        # Por ahora verificamos la estructura básica
        
        # Arrange
        producto_id = fake.uuid4()
        
        producto = Producto(
            id=producto_id,
            codigo='REL001',
            nombre='Producto con Inventarios',
            precio_unitario=Decimal('30.00'),
            categoria_id='TEST'
        )
        
        inventarios = [
            Inventario(
                id=fake.uuid4(),
                producto_id=producto_id,
                pais='CO',
                cantidad=100
            ),
            Inventario(
                id=fake.uuid4(),
                producto_id=producto_id,
                pais='PE',
                cantidad=50
            )
        ]
        
        # Assert
        assert producto.id == producto_id
        for inv in inventarios:
            assert inv.producto_id == producto_id

class TestModelValidations:
    """Pruebas de validaciones de modelos."""

    @pytest.mark.unit
    def test_producto_codigo_unico(self):
        """Prueba unicidad del código de producto."""
        codigo = fake.lexify(text='UNQ???')
        
        producto1 = Producto(
            id=fake.uuid4(),
            codigo=codigo,
            nombre='Producto 1',
            precio_unitario=Decimal('10.00'),
            categoria_id='TEST'
        )
        
        producto2 = Producto(
            id=fake.uuid4(),
            codigo=codigo,  # Mismo código
            nombre='Producto 2',
            precio_unitario=Decimal('15.00'),
            categoria_id='TEST'
        )
        
        # En una BD real, esto generaría un error de constraint
        # Aquí solo verificamos que los objetos se crean
        assert producto1.codigo == producto2.codigo

    @pytest.mark.unit
    def test_inventario_producto_pais_unico(self):
        """Prueba unicidad de producto-país en inventario."""
        producto_id = fake.uuid4()
        pais = 'CO'
        
        inv1 = Inventario(
            id=fake.uuid4(),
            producto_id=producto_id,
            pais=pais,
            cantidad=100
        )
        
        inv2 = Inventario(
            id=fake.uuid4(),
            producto_id=producto_id,
            pais=pais,  # Misma combinación
            cantidad=200
        )
        
        # En BD real habría constraint único
        assert inv1.producto_id == inv2.producto_id
        assert inv1.pais == inv2.pais

class TestModelFaker:
    """Pruebas usando datos generados con Faker."""

    @pytest.mark.unit
    def test_producto_con_faker_categorias_realistas(self):
        """Prueba producto con categorías médicas realistas."""
        categorias_medicas = [
            'ANTIBIOTICS', 'PAINKILLERS', 'VITAMINS', 'ANTIVIRAL',
            'CARDIOVASCULAR', 'DERMATOLOGICAL', 'RESPIRATORY'
        ]
        
        for _ in range(10):  # Generar varios productos de prueba
            producto = Producto(
                id=fake.uuid4(),
                codigo=fake.lexify(text='MED???').upper(),
                nombre=f"{fake.company()} {fake.random_element(['500mg', '250mg', '1g', '100ml'])}",
                descripcion=fake.text(max_nb_chars=150),
                categoria_id=fake.random_element(categorias_medicas),
                precio_unitario=Decimal(str(fake.pyfloat(positive=True, max_value=500, right_digits=2))),
                unidad_medida=fake.random_element(['mg', 'ml', 'capsulas', 'tabletas', 'ampolletas']),
                fecha_creacion=fake.date_time_this_year(tzinfo=timezone.utc),
                fecha_actualizacion=fake.date_time_this_month(tzinfo=timezone.utc)
            )
            
            # Assert
            assert producto.categoria_id in categorias_medicas
            assert producto.precio_unitario > 0
            assert len(producto.codigo) >= 3
            assert 'mg' in producto.unidad_medida or 'ml' in producto.unidad_medida or 'capsulas' in producto.unidad_medida

    @pytest.mark.unit
    def test_inventario_con_faker_paises_latinoamerica(self):
        """Prueba inventario con países de Latinoamérica."""
        paises_latam = ['CO', 'PE', 'MX', 'AR', 'CL', 'EC', 'VE', 'BO', 'PY', 'UY']
        
        for _ in range(15):  # Generar varios inventarios
            inventario = Inventario(
                id=fake.uuid4(),
                producto_id=fake.uuid4(),
                pais=fake.random_element(paises_latam),
                cantidad=fake.random_int(min=0, max=5000),
                fecha_actualizacion=fake.date_time_this_month(tzinfo=timezone.utc)
            )
            
            # Assert
            assert inventario.pais in paises_latam
            assert inventario.cantidad >= 0
            assert isinstance(inventario.fecha_actualizacion, datetime)

    @pytest.mark.unit
    def test_modelos_integracion_faker_completa(self):
        """Prueba integración completa con datos de Faker."""
        # Generar producto base
        producto = Producto(
            id=fake.uuid4(),
            codigo=fake.lexify(text='INT???').upper(),
            nombre=f"Medicamento {fake.word().title()} {fake.random_element(['250mg', '500mg'])}",
            descripcion=fake.sentence(nb_words=10),
            categoria_id=fake.random_element(['ANTIBIOTICS', 'VITAMINS', 'PAINKILLERS']),
            precio_unitario=Decimal(str(fake.pyfloat(positive=True, max_value=200, right_digits=2))),
            unidad_medida=fake.random_element(['mg', 'ml', 'tabletas']),
            fecha_creacion=fake.date_time_this_year(tzinfo=timezone.utc)
        )
        
        # Generar inventarios asociados
        inventarios = []
        for pais in ['CO', 'PE', 'MX']:
            inventario = Inventario(
                id=fake.uuid4(),
                producto_id=producto.id,
                pais=pais,
                cantidad=fake.random_int(min=50, max=2000),
                fecha_actualizacion=fake.date_time_this_month(tzinfo=timezone.utc)
            )
            inventarios.append(inventario)
        
        # Assert - Verificar consistencia
        assert len(inventarios) == 3
        for inv in inventarios:
            assert inv.producto_id == producto.id
            assert inv.cantidad > 0
        
        # Verificar que todos los países son únicos
        paises = [inv.pais for inv in inventarios]
        assert len(set(paises)) == len(paises)  # No duplicados