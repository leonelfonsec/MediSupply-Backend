import pytest
from unittest.mock import patch, AsyncMock
from faker import Faker
import json
from app.cache import search_key

fake = Faker(['es_ES'])

class TestCacheKeyGeneration:
    """Pruebas para generación de claves de caché."""

    @pytest.mark.unit
    def test_search_key_basic(self):
        """Prueba generación básica de clave de búsqueda."""
        # Act
        key = search_key(q="amoxicilina", page=1, size=20)
        
        # Assert
        assert "catalog:search:" in key
        assert "amoxicilina" in key
        assert "p=1" in key
        assert "s=20" in key

    @pytest.mark.unit
    def test_search_key_with_faker(self):
        """Prueba generación de clave con datos de Faker."""
        # Arrange
        query = fake.word()
        categoria = fake.random_element(['ANTIBIOTICS', 'VITAMINS'])
        codigo = fake.lexify(text='MED???')
        pais = fake.country_code()
        
        # Act
        key = search_key(
            q=query,
            categoriaId=categoria,
            codigo=codigo,
            pais=pais,
            page=2,
            size=50
        )
        
        # Assert
        assert f"q={query}" in key
        assert f"cat={categoria}" in key
        assert f"cod={codigo}" in key
        assert f"pais={pais}" in key
        assert "p=2" in key
        assert "s=50" in key

    @pytest.mark.unit
    def test_search_key_empty_values(self):
        """Prueba generación de clave con valores vacíos."""
        # Act
        key = search_key()
        
        # Assert
        assert "catalog:search:" in key
        assert "q=" in key
        assert "cat=" in key
        assert "cod=" in key
        assert "pais=" in key
        assert "p=1" in key  # default
        assert "s=20" in key  # default

    @pytest.mark.unit
    def test_search_key_consistency(self):
        """Prueba que la misma consulta genere la misma clave."""
        # Arrange
        params = {
            "q": fake.word(),
            "categoriaId": "ANTIBIOTICS",
            "page": 1,
            "size": 20
        }
        
        # Act
        key1 = search_key(**params)
        key2 = search_key(**params)
        
        # Assert
        assert key1 == key2

    @pytest.mark.unit
    def test_search_key_different_params(self):
        """Prueba que parámetros diferentes generen claves diferentes."""
        # Arrange
        query = fake.word()
        
        # Act
        key1 = search_key(q=query, page=1, size=20)
        key2 = search_key(q=query, categoriaId="ANTIBIOTICS", page=1, size=20)
        key3 = search_key(q=query, page=2, size=20)
        
        # Assert
        assert key1 != key2
        assert key1 != key3
        assert key2 != key3

class TestCacheKeyVariations:
    """Pruebas para variaciones de claves de caché."""

    @pytest.mark.unit
    def test_search_key_with_special_characters(self):
        """Prueba clave de búsqueda con caracteres especiales."""
        # Arrange
        query_with_spaces = fake.sentence(nb_words=3)
        
        # Act
        key = search_key(q=query_with_spaces)
        
        # Assert
        assert "catalog:search:" in key
        assert query_with_spaces in key

    @pytest.mark.unit
    def test_search_key_pagination_variations(self):
        """Prueba diferentes valores de paginación."""
        pagination_cases = [
            (1, 20),
            (2, 50),
            (10, 100),
            (1, fake.random_int(min=1, max=100))
        ]
        
        for page, size in pagination_cases:
            # Act
            key = search_key(page=page, size=size)
            
            # Assert
            assert f"p={page}" in key
            assert f"s={size}" in key

    @pytest.mark.unit
    def test_search_key_all_parameters(self):
        """Prueba clave con todos los parámetros posibles."""
        # Arrange
        all_params = {
            "q": fake.word(),
            "categoriaId": fake.random_element(['ANTIBIOTICS', 'VITAMINS']),
            "codigo": fake.lexify(text='???'),
            "pais": fake.country_code(),
            "bodegaId": fake.lexify(text='BOD???'),
            "page": fake.random_int(min=1, max=10),
            "size": fake.random_int(min=10, max=100),
            "sort": fake.random_element(['nombre', 'precio', 'codigo'])
        }
        
        # Act
        key = search_key(**all_params)
        
        # Assert
        assert "catalog:search:" in key
        for param_name, param_value in all_params.items():
            if param_name == "categoriaId":
                assert f"cat={param_value}" in key
            elif param_name == "bodegaId":
                assert f"bod={param_value}" in key
            elif param_name == "page":
                assert f"p={param_value}" in key
            elif param_name == "size":
                assert f"s={param_value}" in key
            else:
                assert str(param_value) in key

class TestCacheKeyLogic:
    """Pruebas para lógica de claves de caché."""

    @pytest.mark.unit
    def test_search_key_none_handling(self):
        """Prueba manejo de valores None."""
        # Act
        key = search_key(q=None, categoriaId=None, codigo=None)
        
        # Assert
        assert "q=" in key
        assert "cat=" in key  
        assert "cod=" in key

    @pytest.mark.unit
    def test_search_key_string_conversion(self):
        """Prueba conversión a string de parámetros."""
        # Arrange
        numeric_page = fake.random_int(min=1, max=100)
        numeric_size = fake.random_int(min=1, max=100)
        
        # Act
        key = search_key(page=numeric_page, size=numeric_size)
        
        # Assert
        assert f"p={numeric_page}" in key
        assert f"s={numeric_size}" in key

    @pytest.mark.unit
    def test_search_key_order_independence(self):
        """Prueba que el orden de parámetros no afecte la clave."""
        # Arrange
        query = fake.word()
        categoria = "ANTIBIOTICS"
        
        # Act - Mismos parámetros, orden diferente en el código
        key1 = search_key(q=query, categoriaId=categoria, page=1, size=20)
        key2 = search_key(page=1, size=20, q=query, categoriaId=categoria)
        
        # Assert
        assert key1 == key2

class TestCacheKeyEdgeCases:
    """Pruebas para casos límite en claves de caché."""

    @pytest.mark.unit  
    def test_search_key_empty_string_vs_none(self):
        """Prueba diferencia entre string vacío y None."""
        # Act
        key_none = search_key(q=None)
        key_empty = search_key(q="")
        
        # Assert
        # Ambos deberían comportarse igual (q=)
        assert "q=" in key_none
        assert "q=" in key_empty

    @pytest.mark.unit
    def test_search_key_minimum_values(self):
        """Prueba con valores mínimos."""
        # Act
        key = search_key(page=1, size=1)
        
        # Assert
        assert "p=1" in key
        assert "s=1" in key

    @pytest.mark.unit
    def test_search_key_realistic_scenarios(self):
        """Prueba escenarios realistas con Faker."""
        scenarios = [
            # Búsqueda simple
            {"q": fake.word()},
            # Búsqueda por categoría
            {"categoriaId": "ANTIBIOTICS"},
            # Búsqueda por código
            {"codigo": fake.lexify(text='MED???')},
            # Búsqueda paginada
            {"q": fake.word(), "page": 2, "size": 50},
            # Búsqueda completa
            {
                "q": fake.word(),
                "categoriaId": "VITAMINS", 
                "pais": "CO",
                "page": 1,
                "size": 20
            }
        ]
        
        for scenario in scenarios:
            # Act
            key = search_key(**scenario)
            
            # Assert
            assert key.startswith("catalog:search:")
            assert len(key) > len("catalog:search:")
            
            # Verificar que contiene información relevante
            for param_name, param_value in scenario.items():
                assert str(param_value) in key or param_value in key