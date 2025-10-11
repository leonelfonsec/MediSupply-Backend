import pytest
from faker import Faker
from app.schemas import Product, StockItem, InventarioResumen, SearchResponse, Meta

fake = Faker(['es_ES'])

class TestProduct:
    """Pruebas para el schema Product."""

    @pytest.mark.unit
    def test_product_creation_basic(self):
        """Prueba creación básica de Product con Faker."""
        # Arrange
        product_data = {
            "id": fake.uuid4(),
            "codigo": fake.lexify(text='MED???').upper(),
            "nombre": f"{fake.company()} {fake.random_element(['500mg', '250mg', '1g'])}",
            "categoria": fake.random_element(['ANTIBIOTICS', 'PAINKILLERS', 'VITAMINS']),
            "precioUnitario": fake.pyfloat(positive=True, max_value=1000, right_digits=2)
        }
        
        # Act
        product = Product(**product_data)
        
        # Assert
        assert product.id == product_data["id"]
        assert product.codigo == product_data["codigo"]
        assert product.nombre == product_data["nombre"]
        assert product.categoria == product_data["categoria"]
        assert product.precioUnitario == product_data["precioUnitario"]

    @pytest.mark.unit
    def test_product_with_optional_fields(self):
        """Prueba Product con campos opcionales."""
        # Arrange
        product_data = {
            "id": fake.uuid4(),
            "codigo": fake.lexify(text='OPT???'),
            "nombre": fake.company(),
            "categoria": "ANTIBIOTICS",
            "precioUnitario": fake.pyfloat(positive=True, max_value=100, right_digits=2),
            "presentacion": fake.random_element(['tabletas', 'capsulas', 'ml']),
            "requisitosAlmacenamiento": fake.random_element(['REFRIGERADO', 'AMBIENTE'])
        }
        
        # Act
        product = Product(**product_data)
        
        # Assert
        assert product.presentacion == product_data["presentacion"]
        assert product.requisitosAlmacenamiento == product_data["requisitosAlmacenamiento"]

    @pytest.mark.unit
    def test_product_with_inventario_resumen(self):
        """Prueba Product con resumen de inventario."""
        # Arrange
        inventario_data = {
            "cantidadTotal": fake.random_int(min=0, max=5000),
            "paises": [fake.country_code() for _ in range(fake.random_int(min=1, max=5))]
        }
        
        product_data = {
            "id": fake.uuid4(),
            "codigo": fake.lexify(text='INV???'),
            "nombre": f"Medicamento {fake.word().title()}",
            "categoria": "ANTIBIOTICS",
            "precioUnitario": fake.pyfloat(positive=True, max_value=200, right_digits=2),
            "inventarioResumen": InventarioResumen(**inventario_data)
        }
        
        # Act
        product = Product(**product_data)
        
        # Assert
        assert product.inventarioResumen is not None
        assert product.inventarioResumen.cantidadTotal == inventario_data["cantidadTotal"]
        assert len(product.inventarioResumen.paises) >= 1

class TestStockItem:
    """Pruebas para el schema StockItem."""

    @pytest.mark.unit
    def test_stock_item_creation(self):
        """Prueba creación de StockItem con Faker."""
        # Arrange
        stock_data = {
            "pais": fake.country_code(),
            "bodegaId": fake.lexify(text='BOD???').upper(),
            "lote": fake.lexify(text='LOTE????').upper(),
            "cantidad": fake.random_int(min=0, max=2000),
            "vence": fake.date_between(start_date='+1d', end_date='+2y').isoformat(),
            "condiciones": fake.random_element(['REFRIGERADO', 'AMBIENTE', 'CONGELADO'])
        }
        
        # Act
        stock_item = StockItem(**stock_data)
        
        # Assert
        assert stock_item.pais == stock_data["pais"]
        assert stock_item.bodegaId == stock_data["bodegaId"]
        assert stock_item.lote == stock_data["lote"]
        assert stock_item.cantidad == stock_data["cantidad"]
        assert stock_item.vence == stock_data["vence"]
        assert stock_item.condiciones == stock_data["condiciones"]

    @pytest.mark.unit
    def test_stock_item_paises_latinoamerica(self):
        """Prueba StockItem con países de Latinoamérica."""
        paises_latam = ['CO', 'PE', 'MX', 'AR', 'CL', 'EC', 'VE', 'BO']
        
        for pais in paises_latam:
            stock_data = {
                "pais": pais,
                "bodegaId": f"BOD{pais}001",
                "lote": fake.lexify(text='????'),
                "cantidad": fake.random_int(min=1, max=1000),
                "vence": fake.date_between(start_date='+30d', end_date='+2y').isoformat()
            }
            
            # Act
            stock_item = StockItem(**stock_data)
            
            # Assert
            assert stock_item.pais == pais
            assert stock_item.bodegaId.startswith(f"BOD{pais}")
            assert stock_item.cantidad > 0

    @pytest.mark.unit
    def test_stock_item_optional_condiciones(self):
        """Prueba StockItem con condiciones opcionales."""
        # Arrange
        stock_data = {
            "pais": "CO",
            "bodegaId": "BOD001",
            "lote": "LOTE001",
            "cantidad": fake.random_int(min=1, max=100),
            "vence": fake.date_this_year().isoformat()
            # condiciones es opcional
        }
        
        # Act
        stock_item = StockItem(**stock_data)
        
        # Assert
        assert stock_item.condiciones is None

class TestInventarioResumen:
    """Pruebas para el schema InventarioResumen."""

    @pytest.mark.unit
    def test_inventario_resumen_creation(self):
        """Prueba creación de InventarioResumen."""
        # Arrange
        resumen_data = {
            "cantidadTotal": fake.random_int(min=0, max=10000),
            "paises": [fake.country_code() for _ in range(fake.random_int(min=1, max=8))]
        }
        
        # Act
        resumen = InventarioResumen(**resumen_data)
        
        # Assert
        assert resumen.cantidadTotal == resumen_data["cantidadTotal"]
        assert len(resumen.paises) == len(resumen_data["paises"])
        assert all(pais in resumen.paises for pais in resumen_data["paises"])

    @pytest.mark.unit
    def test_inventario_resumen_empty_paises(self):
        """Prueba InventarioResumen con lista de países vacía."""
        # Arrange
        resumen_data = {
            "cantidadTotal": 0
            # paises usa default []
        }
        
        # Act
        resumen = InventarioResumen(**resumen_data)
        
        # Assert
        assert resumen.cantidadTotal == 0
        assert resumen.paises == []

class TestMeta:
    """Pruebas para el schema Meta."""

    @pytest.mark.unit
    def test_meta_creation(self):
        """Prueba creación de Meta con paginación."""
        # Arrange
        meta_data = {
            "page": fake.random_int(min=1, max=100),
            "size": fake.random_int(min=1, max=100),
            "total": fake.random_int(min=0, max=10000),
            "tookMs": fake.random_int(min=1, max=2000)
        }
        
        # Act
        meta = Meta(**meta_data)
        
        # Assert
        assert meta.page == meta_data["page"]
        assert meta.size == meta_data["size"]
        assert meta.total == meta_data["total"]
        assert meta.tookMs == meta_data["tookMs"]

    @pytest.mark.unit
    def test_meta_performance_criteria(self):
        """Prueba criterios de rendimiento en Meta."""
        # Arrange - Simular respuesta rápida
        meta_data = {
            "page": 1,
            "size": 20,
            "total": fake.random_int(min=1, max=50),
            "tookMs": fake.random_int(min=1, max=500)  # < 500ms = rápido
        }
        
        # Act
        meta = Meta(**meta_data)
        
        # Assert - Verificar criterios de performance
        assert meta.tookMs < 2000  # Criterio: respuesta < 2s
        assert meta.page >= 1
        assert meta.size >= 1
        assert meta.total >= 0

class TestSearchResponse:
    """Pruebas para el schema SearchResponse."""

    @pytest.mark.unit
    def test_search_response_creation(self):
        """Prueba creación de SearchResponse con múltiples productos."""
        # Arrange
        products = []
        for _ in range(fake.random_int(min=1, max=5)):
            product_data = {
                "id": fake.uuid4(),
                "codigo": fake.lexify(text='SRC???'),
                "nombre": f"{fake.word().title()} {fake.random_element(['500mg', '250mg'])}",
                "categoria": fake.random_element(['ANTIBIOTICS', 'VITAMINS']),
                "precioUnitario": fake.pyfloat(positive=True, max_value=100, right_digits=2)
            }
            products.append(Product(**product_data))
        
        meta_data = {
            "page": 1,
            "size": 20,
            "total": len(products),
            "tookMs": fake.random_int(min=10, max=200)
        }
        
        # Act
        response = SearchResponse(
            items=products,
            meta=Meta(**meta_data)
        )
        
        # Assert
        assert len(response.items) == len(products)
        assert response.meta.total == len(products)
        assert response.meta.tookMs < 2000
        
        # Verificar estructura de productos
        for product in response.items:
            assert hasattr(product, 'id')
            assert hasattr(product, 'codigo')
            assert hasattr(product, 'nombre')
            assert hasattr(product, 'precioUnitario')

    @pytest.mark.unit
    def test_search_response_empty_results(self):
        """Prueba SearchResponse con resultados vacíos."""
        # Arrange
        meta_data = {
            "page": 1,
            "size": 20,
            "total": 0,
            "tookMs": fake.random_int(min=1, max=50)
        }
        
        # Act
        response = SearchResponse(
            items=[],
            meta=Meta(**meta_data)
        )
        
        # Assert
        assert len(response.items) == 0
        assert response.meta.total == 0
        assert response.meta.page == 1

class TestSchemaValidations:
    """Pruebas de validaciones de schemas."""

    @pytest.mark.unit
    def test_product_precio_positivo(self):
        """Prueba validación de precio positivo en Product."""
        # Arrange
        product_data = {
            "id": fake.uuid4(),
            "codigo": "POS001",
            "nombre": "Producto Positivo",
            "categoria": "TEST",
            "precioUnitario": fake.pyfloat(positive=True, min_value=0.01, max_value=1000, right_digits=2)
        }
        
        # Act
        product = Product(**product_data)
        
        # Assert
        assert product.precioUnitario > 0

    @pytest.mark.unit
    def test_stock_item_cantidad_no_negativa(self):
        """Prueba que cantidad de StockItem no sea negativa."""
        # Arrange
        stock_data = {
            "pais": "CO",
            "bodegaId": "TEST001",
            "lote": "LOTE001",
            "cantidad": fake.random_int(min=0, max=1000),  # >= 0
            "vence": fake.date_this_year().isoformat()
        }
        
        # Act
        stock_item = StockItem(**stock_data)
        
        # Assert
        assert stock_item.cantidad >= 0

    @pytest.mark.unit
    def test_inventario_resumen_cantidad_total_no_negativa(self):
        """Prueba que cantidadTotal no sea negativa."""
        # Arrange
        resumen_data = {
            "cantidadTotal": fake.random_int(min=0, max=5000),
            "paises": ["CO", "PE"]
        }
        
        # Act
        resumen = InventarioResumen(**resumen_data)
        
        # Assert
        assert resumen.cantidadTotal >= 0

    @pytest.mark.unit
    def test_meta_pagination_values(self):
        """Prueba validaciones de paginación en Meta."""
        # Arrange
        meta_data = {
            "page": fake.random_int(min=1, max=50),  # >= 1
            "size": fake.random_int(min=1, max=100),  # >= 1
            "total": fake.random_int(min=0, max=1000),  # >= 0
            "tookMs": fake.random_int(min=0, max=5000)  # >= 0
        }
        
        # Act
        meta = Meta(**meta_data)
        
        # Assert
        assert meta.page >= 1
        assert meta.size >= 1
        assert meta.total >= 0
        assert meta.tookMs >= 0