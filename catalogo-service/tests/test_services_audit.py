"""
Pruebas unitarias completas para app/services/audit.py
Objetivo: 100% de cobertura del servicio de auditoría
"""

import pytest
from unittest.mock import AsyncMock, Mock
import json
from faker import Faker
from app.services.audit import audit_log

fake = Faker()

class TestAuditLog:
    """Pruebas para la función audit_log"""
    
    @pytest.fixture
    def mock_session(self):
        """Mock de la sesión AsyncSession"""
        return AsyncMock()
    
    @pytest.fixture
    def sample_audit_data(self):
        """Datos de auditoría de ejemplo usando Faker"""
        return {
            "user_id": fake.uuid4(),
            "endpoint": "/catalog/items",
            "filtros": {
                "q": fake.word(),
                "categoriaId": fake.uuid4(),
                "page": fake.random_int(min=1, max=10),
                "size": fake.random_int(min=10, max=50)
            },
            "took_ms": fake.random_int(min=1, max=1000),
            "canal": fake.random_element(["web", "mobile", "api"])
        }
    
    async def test_audit_log_completo(self, mock_session, sample_audit_data):
        """Prueba registro de auditoría con todos los campos"""
        # Act
        await audit_log(
            session=mock_session,
            user_id=sample_audit_data["user_id"],
            endpoint=sample_audit_data["endpoint"],
            filtros=sample_audit_data["filtros"],
            took_ms=sample_audit_data["took_ms"],
            canal=sample_audit_data["canal"]
        )
        
        # Assert
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()
        
        # Verificar parámetros de la consulta SQL
        call_args = mock_session.execute.call_args
        sql_query = call_args[0][0]
        parameters = call_args[0][1]
        
        # Verificar que contiene la consulta correcta
        assert "INSERT INTO consulta_catalogo_log" in str(sql_query)
        assert "user_id, endpoint, filtros, took_ms, canal" in str(sql_query)
        
        # Verificar parámetros
        assert parameters["u"] == sample_audit_data["user_id"]
        assert parameters["e"] == sample_audit_data["endpoint"]
        assert parameters["f"] == json.dumps(sample_audit_data["filtros"])
        assert parameters["t"] == sample_audit_data["took_ms"]
        assert parameters["c"] == sample_audit_data["canal"]
    
    async def test_audit_log_sin_user_id(self, mock_session):
        """Prueba registro de auditoría sin user_id"""
        # Arrange
        test_data = {
            "user_id": None,
            "endpoint": "/catalog/items/search",
            "filtros": {"q": fake.word()},
            "took_ms": fake.random_int(min=50, max=200),
            "canal": "anonymous"
        }
        
        # Act
        await audit_log(
            session=mock_session,
            user_id=test_data["user_id"],
            endpoint=test_data["endpoint"],
            filtros=test_data["filtros"],
            took_ms=test_data["took_ms"],
            canal=test_data["canal"]
        )
        
        # Assert
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()
        
        # Verificar que user_id es None
        call_args = mock_session.execute.call_args
        parameters = call_args[0][1]
        assert parameters["u"] is None
    
    async def test_audit_log_filtros_vacios(self, mock_session):
        """Prueba registro con filtros vacíos"""
        # Arrange
        test_data = {
            "user_id": fake.uuid4(),
            "endpoint": "/catalog/items",
            "filtros": {},  # Filtros vacíos
            "took_ms": fake.random_int(min=1, max=50),
            "canal": "web"
        }
        
        # Act
        await audit_log(
            session=mock_session,
            user_id=test_data["user_id"],
            endpoint=test_data["endpoint"],
            filtros=test_data["filtros"],
            took_ms=test_data["took_ms"],
            canal=test_data["canal"]
        )
        
        # Assert
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()
        
        # Verificar que se serializa como JSON vacío
        call_args = mock_session.execute.call_args
        parameters = call_args[0][1]
        assert parameters["f"] == json.dumps({})
    
    async def test_audit_log_filtros_complejos(self, mock_session):
        """Prueba registro con filtros complejos"""
        # Arrange
        filtros_complejos = {
            "q": fake.sentence(),
            "categoriaId": fake.uuid4(),
            "codigo": fake.bothify("MED-####"),
            "pais": fake.country_code(),
            "bodegaId": fake.bothify("BOD-###"),
            "page": fake.random_int(min=1, max=100),
            "size": fake.random_int(min=10, max=100),
            "sort": fake.random_element(["precio", "nombre", "relevancia"]),
            "metadata": {
                "source": fake.random_element(["search", "filter", "category"]),
                "timestamp": fake.iso8601(),
                "nested": {
                    "level": fake.random_int(min=1, max=5),
                    "items": [fake.word() for _ in range(3)]
                }
            }
        }
        
        test_data = {
            "user_id": fake.uuid4(),
            "endpoint": "/catalog/items/advanced-search",
            "filtros": filtros_complejos,
            "took_ms": fake.random_int(min=100, max=2000),
            "canal": "api"
        }
        
        # Act
        await audit_log(
            session=mock_session,
            user_id=test_data["user_id"],
            endpoint=test_data["endpoint"],
            filtros=test_data["filtros"],
            took_ms=test_data["took_ms"],
            canal=test_data["canal"]
        )
        
        # Assert
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()
        
        # Verificar que se serializa correctamente el JSON complejo
        call_args = mock_session.execute.call_args
        parameters = call_args[0][1]
        
        # Deserializar y verificar que es igual al original
        stored_filtros = json.loads(parameters["f"])
        assert stored_filtros == filtros_complejos
    
    async def test_audit_log_diferentes_endpoints(self, mock_session):
        """Prueba registro para diferentes endpoints"""
        # Arrange
        endpoints_test = [
            "/catalog/items",
            "/catalog/items/search",
            "/catalog/items/{id}",
            "/catalog/items/{id}/inventario",
            "/catalog/categories"
        ]
        
        for endpoint in endpoints_test:
            # Act
            await audit_log(
                session=mock_session,
                user_id=fake.uuid4(),
                endpoint=endpoint,
                filtros={"test": fake.word()},
                took_ms=fake.random_int(min=1, max=100),
                canal=fake.random_element(["web", "mobile"])
            )
        
        # Assert
        assert mock_session.execute.call_count == len(endpoints_test)
        assert mock_session.commit.call_count == len(endpoints_test)
    
    async def test_audit_log_diferentes_canales(self, mock_session):
        """Prueba registro para diferentes canales"""
        # Arrange
        canales_test = ["web", "mobile", "api", "desktop", "tablet", "cli"]
        
        for canal in canales_test:
            # Act
            await audit_log(
                session=mock_session,
                user_id=fake.uuid4(),
                endpoint="/catalog/test",
                filtros={"canal_test": canal},
                took_ms=fake.random_int(min=1, max=100),
                canal=canal
            )
        
        # Assert
        assert mock_session.execute.call_count == len(canales_test)
        assert mock_session.commit.call_count == len(canales_test)
    
    async def test_audit_log_tiempo_respuesta_variado(self, mock_session):
        """Prueba registro con diferentes tiempos de respuesta"""
        # Arrange
        tiempos_test = [1, 50, 100, 500, 1000, 2500, 5000]
        
        for tiempo in tiempos_test:
            # Act
            await audit_log(
                session=mock_session,
                user_id=fake.uuid4(),
                endpoint=f"/catalog/performance-test/{tiempo}",
                filtros={"performance_test": True, "expected_time": tiempo},
                took_ms=tiempo,
                canal="performance"
            )
        
        # Assert
        assert mock_session.execute.call_count == len(tiempos_test)
        assert mock_session.commit.call_count == len(tiempos_test)
        
        # Verificar que los tiempos se guardaron correctamente
        for i, call in enumerate(mock_session.execute.call_args_list):
            parameters = call[0][1]
            assert parameters["t"] == tiempos_test[i]
    
    async def test_audit_log_casos_edge(self, mock_session):
        """Prueba casos edge y límites"""
        # Arrange & Act & Assert
        
        # Caso 1: Tiempo 0
        await audit_log(
            session=mock_session,
            user_id=fake.uuid4(),
            endpoint="/catalog/instant",
            filtros={"instant": True},
            took_ms=0,
            canal="instant"
        )
        
        # Caso 2: String muy largo en endpoint
        long_endpoint = "/catalog/" + "very-long-path/" * 20
        await audit_log(
            session=mock_session,
            user_id=fake.uuid4(),
            endpoint=long_endpoint,
            filtros={"long_path": True},
            took_ms=fake.random_int(min=1, max=100),
            canal="long"
        )
        
        # Caso 3: Filtros con caracteres especiales
        special_filtros = {
            "special_chars": "áéíóú ñÑ !@#$%^&*()_+-={}[]|\\:;\"'<>?,./",
            "unicode": "🔍 🏥 💊 📦",
            "json_chars": '{"nested": "value", "array": [1,2,3]}'
        }
        await audit_log(
            session=mock_session,
            user_id=fake.uuid4(),
            endpoint="/catalog/special",
            filtros=special_filtros,
            took_ms=fake.random_int(min=1, max=100),
            canal="special"
        )
        
        # Verificar que todas las llamadas se ejecutaron
        assert mock_session.execute.call_count == 3
        assert mock_session.commit.call_count == 3


class TestAuditIntegration:
    """Pruebas de integración para auditoría"""
    
    async def test_audit_log_flujo_realista(self):
        """Prueba un flujo realista de auditoría"""
        # Arrange
        mock_session = AsyncMock()
        
        # Simular una búsqueda real
        user_id = fake.uuid4()
        search_query = fake.word()
        categoria = fake.uuid4()
        
        filtros_busqueda = {
            "q": search_query,
            "categoriaId": categoria,
            "page": 1,
            "size": 20,
            "sort": "relevancia"
        }
        
        # Act
        await audit_log(
            session=mock_session,
            user_id=user_id,
            endpoint="/catalog/items",
            filtros=filtros_busqueda,
            took_ms=150,
            canal="web"
        )
        
        # Assert
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()
        
        # Verificar que los datos se almacenan correctamente
        call_args = mock_session.execute.call_args
        parameters = call_args[0][1]
        
        assert parameters["u"] == user_id
        assert parameters["e"] == "/catalog/items"
        assert json.loads(parameters["f"]) == filtros_busqueda
        assert parameters["t"] == 150
        assert parameters["c"] == "web"