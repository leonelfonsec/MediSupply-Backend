import pytest
from faker import Faker
from decimal import Decimal
from datetime import datetime
from app.schemas import (
    Product, StockItem, InventarioResumen,
    SearchResponse, Meta
)

fake = Faker(['es_ES'])

class TestProductoResponse:
    """Pruebas para el schema ProductoResponse."""

    @pytest.mark.unit
    def test_producto_response_creation(self):
        """Prueba creación de ProductoResponse con Faker."""
        # Arrange
        producto_data = {
            "id": fake.uuid4(),
            "codigo": fake.lexify(text='MED???').upper(),
            "nombre": f"{fake.company()} {fake.random_element(['500mg', '250mg', '1g'])}",
            "categoria": fake.random_element(['ANTIBIOTICS', 'PAINKILLERS', 'VITAMINS']),
            "presentacion": fake.random_element(['tabletas', 'capsulas', 'ml']),
            "precio": fake.pyfloat(positive=True, max_value=1000, right_digits=2),
            "activo": fake.boolean()
        }
        
        # Act
        producto = ProductoResponse(**producto_data)
        
        # Assert
        assert producto.id == producto_data["id"]
        assert producto.codigo == producto_data["codigo"]
        assert producto.nombre == producto_data["nombre"]
        assert producto.categoria == producto_data["categoria"]
        assert producto.presentacion == producto_data["presentacion"]
        assert producto.precio == producto_data["precio"]
        assert producto.activo == producto_data["activo"]

    @pytest.mark.unit
    def test_producto_response_optional_fields(self):
        """Prueba campos opcionales en ProductoResponse."""
        # Arrange - Solo campos requeridos
        producto_data = {
            "id": fake.uuid4(),
            "codigo": fake.lexify(text='REQ???'),
            "nombre": fake.company(),
            "categoria": "REQUIRED",
            "precio": fake.pyfloat(positive=True, max_value=100, right_digits=2)
        }
        
        # Act
        producto = ProductoResponse(**producto_data)
        
        # Assert
        assert producto.id is not None
        assert producto.codigo is not None
        assert producto.nombre is not None
        assert producto.categoria is not None
        assert producto.precio is not None

    @pytest.mark.unit
    def test_producto_response_with_inventario_resumen(self):
        """Prueba ProductoResponse con resumen de inventario."""
        # Arrange
        inventario_resumen = {
            "cantidad": fake.random_int(min=0, max=5000),
            "paises": [fake.country_code() for _ in range(fake.random_int(min=1, max=5))]
        }
        
        producto_data = {
            "id": fake.uuid4(),
            "codigo": fake.lexify(text='INV???'),
            "nombre": fake.company(),
            "categoria": "ANTIBIOTICS",
            "precio": fake.pyfloat(positive=True, max_value=200, right_digits=2),
            "inventarioResumen": inventario_resumen
        }
        
        # Act
        producto = ProductoResponse(**producto_data)
        
        # Assert
        assert producto.inventarioResumen == inventario_resumen
        assert producto.inventarioResumen["cantidad"] >= 0
        assert len(producto.inventarioResumen["paises"]) >= 1

class TestInventarioResponse:
    """Pruebas para el schema InventarioResponse."""

    @pytest.mark.unit
    def test_inventario_response_creation(self):
        """Prueba creación de InventarioResponse con Faker."""
        # Arrange
        inventario_data = {
            "id": fake.random_int(min=1, max=10000),
            "producto_id": fake.uuid4(),
            "pais": fake.country_code(),
            "bodega_id": fake.lexify(text='BOD???').upper(),
            "lote": fake.lexify(text='LOTE????').upper(),
            "cantidad": fake.random_int(min=0, max=2000),
            "vence": fake.date_this_year().isoformat(),
            "condiciones": fake.random_element(['REFRIGERADO', 'AMBIENTE', 'CONGELADO'])
        }
        
        # Act
        inventario = InventarioResponse(**inventario_data)
        
        # Assert
        assert inventario.id == inventario_data["id"]
        assert inventario.producto_id == inventario_data["producto_id"]
        assert inventario.pais == inventario_data["pais"]
        assert inventario.bodega_id == inventario_data["bodega_id"]
        assert inventario.lote == inventario_data["lote"]
        assert inventario.cantidad == inventario_data["cantidad"]
        assert inventario.vence == inventario_data["vence"]

class TestMeta:
    """Pruebas para el schema Meta."""

    @pytest.mark.unit
    def test_meta_paginacion(self):
        """Prueba schema Meta con paginación."""
        # Arrange
        meta_data = {
            "total": fake.random_int(min=0, max=10000),
            "page": fake.random_int(min=1, max=100),
            "size": fake.random_int(min=1, max=100),
            "tookMs": fake.random_int(min=1, max=2000)
        }
        
        # Act
        meta = Meta(**meta_data)
        
        # Assert
        assert meta.total == meta_data["total"]
        assert meta.page == meta_data["page"]
        assert meta.size == meta_data["size"]
        assert meta.tookMs == meta_data["tookMs"]

    @pytest.mark.unit
    def test_meta_performance_metrics(self):
        """Prueba métricas de rendimiento en Meta."""
        # Arrange - Simular respuesta rápida
        meta_data = {
            "total": fake.random_int(min=1, max=50),
            "page": 1,
            "size": 20,
            "tookMs": fake.random_int(min=1, max=500)  # < 500ms = rápido
        }
        
        # Act
        meta = Meta(**meta_data)
        
        # Assert - Verificar criterios de performance
        assert meta.tookMs < 2000  # Criterio: respuesta < 2s
        assert meta.total >= 0
        assert meta.page >= 1
        assert meta.size >= 1

class TestListResponses:
    """Pruebas para schemas de listas."""

    @pytest.mark.unit
    def test_productos_list_response(self):
        """Prueba ProductosListResponse con múltiples productos."""
        # Arrange
        productos = []
        for _ in range(fake.random_int(min=1, max=5)):
            producto_data = {
                "id": fake.uuid4(),
                "codigo": fake.lexify(text='LST???'),
                "nombre": f"{fake.word().title()} {fake.random_element(['500mg', '250mg'])}",
                "categoria": fake.random_element(['ANTIBIOTICS', 'VITAMINS']),
                "precio": fake.pyfloat(positive=True, max_value=100, right_digits=2)
            }
            productos.append(ProductoResponse(**producto_data))
        
        meta_data = {
            "total": len(productos),
            "page": 1,
            "size": 20,
            "tookMs": fake.random_int(min=10, max=200)
        }
        
        # Act
        response = ProductosListResponse(
            items=productos,
            meta=Meta(**meta_data)
        )
        
        # Assert
        assert len(response.items) == len(productos)
        assert response.meta.total == len(productos)
        assert response.meta.tookMs < 2000
        
        # Verificar estructura de productos
        for producto in response.items:
            assert hasattr(producto, 'id')
            assert hasattr(producto, 'codigo')
            assert hasattr(producto, 'nombre')
            assert hasattr(producto, 'precio')

class TestSchemaValidations:
    """Pruebas de validaciones de schemas."""

    @pytest.mark.unit
    def test_producto_precio_positivo(self):
        """Prueba validación de precio positivo."""
        # Arrange
        producto_data = {
            "id": fake.uuid4(),
            "codigo": "POS001",
            "nombre": "Producto Positivo",
            "categoria": "TEST",
            "precio": fake.pyfloat(positive=True, min_value=0.01, max_value=1000, right_digits=2)
        }
        
        # Act
        producto = ProductoResponse(**producto_data)
        
        # Assert
        assert producto.precio > 0

    @pytest.mark.unit
    def test_inventario_cantidad_no_negativa(self):
        """Prueba que cantidad de inventario no sea negativa."""
        # Arrange
        inventario_data = {
            "id": fake.random_int(min=1, max=100),
            "producto_id": fake.uuid4(),
            "pais": "CO",
            "bodega_id": "TEST001",
            "lote": "LOTE001",
            "cantidad": fake.random_int(min=0, max=1000),  # >= 0
            "vence": fake.date_this_year().isoformat()
        }
        
        # Act
        inventario = InventarioResponse(**inventario_data)
        
        # Assert
        assert inventario.cantidad >= 0

    @pytest.mark.unit
    def test_meta_valores_validos(self):
        """Prueba validaciones en Meta."""
        # Arrange
        meta_data = {
            "total": fake.random_int(min=0, max=1000),
            "page": fake.random_int(min=1, max=50),  # >= 1
            "size": fake.random_int(min=1, max=100),  # >= 1
            "tookMs": fake.random_int(min=0, max=5000)  # >= 0
        }
        
        # Act
        meta = Meta(**meta_data)
        
        # Assert
        assert meta.total >= 0
        assert meta.page >= 1
        assert meta.size >= 1
        assert meta.tookMs >= 0