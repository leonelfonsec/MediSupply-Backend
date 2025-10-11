import pytest
from unittest.mock import patch
import os
from faker import Faker
from app.config import Settings

fake = Faker()

class TestSettings:
    """Pruebas para la configuración de la aplicación."""

    @pytest.mark.unit
    def test_configuracion_default(self):
        """Prueba configuración con valores por defecto."""
        # Act
        settings = Settings()
        
        # Assert
        assert settings.DATABASE_URL is not None
        assert settings.REDIS_URL is not None
        assert settings.page_size_default == 20
        assert settings.page_size_max == 50

    @pytest.mark.unit
    def test_configuracion_desde_variables_entorno(self):
        """Prueba configuración desde variables de entorno."""
        # Arrange
        test_database_url = fake.url()
        test_redis_url = f"redis://{fake.ipv4()}:6379/1"
        
        with patch.dict(os.environ, {
            'DATABASE_URL': test_database_url,
            'REDIS_URL': test_redis_url,
            'PAGE_SIZE_DEFAULT': '25',
            'PAGE_SIZE_MAX': '75'
        }):
            # Act
            settings = Settings()
            
            # Assert
            assert settings.DATABASE_URL == test_database_url
            assert settings.REDIS_URL == test_redis_url
            assert settings.page_size_default == 25
            assert settings.page_size_max == 75

    @pytest.mark.unit
    def test_configuracion_variables_extra_permitidas(self):
        """Prueba que se permitan variables de entorno extra."""
        # Arrange
        with patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://test:test@localhost/testdb',
            'EXTRA_VAR': 'extra_value',
            'ANOTHER_VAR': '123'
        }):
            # Act & Assert - No debería lanzar error
            try:
                settings = Settings()
                success = True
            except Exception:
                success = False
            
            assert success

    @pytest.mark.unit
    def test_validacion_page_size(self):
        """Prueba validación de tamaños de página."""
        # Arrange & Act
        with patch.dict(os.environ, {
            'PAGE_SIZE_DEFAULT': '10',
            'PAGE_SIZE_MAX': '200'
        }):
            settings = Settings()
            
            # Assert
            assert settings.page_size_default == 10
            assert settings.page_size_max == 200

    @pytest.mark.unit
    def test_configuracion_database_url_formatos(self):
        """Prueba diferentes formatos de DATABASE_URL."""
        test_cases = [
            "postgresql://user:pass@localhost:5432/dbname",
            "postgresql+asyncpg://user:pass@host:5432/db",
            "postgresql://user@localhost/dbname"
        ]
        
        for db_url in test_cases:
            with patch.dict(os.environ, {'DATABASE_URL': db_url}):
                # Act
                settings = Settings()
                
                # Assert
                assert settings.DATABASE_URL == db_url

    @pytest.mark.unit
    def test_configuracion_redis_url_formatos(self):
        """Prueba diferentes formatos de REDIS_URL."""
        test_cases = [
            "redis://localhost:6379/0",
            "redis://user:pass@host:6379/1",
            f"redis://{fake.ipv4()}:6379/2"
        ]
        
        for redis_url in test_cases:
            with patch.dict(os.environ, {'REDIS_URL': redis_url}):
                # Act
                settings = Settings()
                
                # Assert
                assert settings.REDIS_URL == redis_url

    @pytest.mark.unit
    def test_configuracion_api_prefix(self):
        """Prueba configuración del prefijo de API."""
        # Act
        settings = Settings()
        
        # Assert
        assert settings.api_prefix == "/api"

class TestSettingsIntegration:
    """Pruebas de integración para configuración."""

    @pytest.mark.unit
    def test_configuracion_completa_desarrollo(self):
        """Prueba configuración completa para desarrollo."""
        # Arrange
        dev_config = {
            'DATABASE_URL': 'postgresql+asyncpg://catalog_user:catalog_pass@localhost:5433/catalog_db',
            'REDIS_URL': 'redis://localhost:6379/1',
            'PAGE_SIZE_DEFAULT': '20',
            'PAGE_SIZE_MAX': '100'
        }
        
        with patch.dict(os.environ, dev_config):
            # Act
            settings = Settings()
            
            # Assert
            assert 'catalog_db' in settings.DATABASE_URL
            assert 'localhost:5433' in settings.DATABASE_URL
            assert '/1' in settings.REDIS_URL
            assert settings.page_size_default == 20
            assert settings.page_size_max == 100

    @pytest.mark.unit
    def test_configuracion_completa_produccion(self):
        """Prueba configuración completa para producción."""
        # Arrange - Simular configuración de producción
        prod_host = fake.domain_name()
        prod_config = {
            'DATABASE_URL': f'postgresql+asyncpg://prod_user:prod_pass@{prod_host}:5432/catalog_prod',
            'REDIS_URL': f'redis://redis.{prod_host}:6379/0',
            'PAGE_SIZE_DEFAULT': '50',
            'PAGE_SIZE_MAX': '200'
        }
        
        with patch.dict(os.environ, prod_config):
            # Act
            settings = Settings()
            
            # Assert
            assert prod_host in settings.DATABASE_URL
            assert 'catalog_prod' in settings.DATABASE_URL
            assert prod_host in settings.REDIS_URL
            assert settings.page_size_default == 50
            assert settings.page_size_max == 200

    @pytest.mark.unit
    def test_singleton_settings_instance(self):
        """Prueba que Settings mantenga consistencia."""
        # Act
        settings1 = Settings()
        settings2 = Settings()
        
        # Assert - Deberían tener los mismos valores
        assert settings1.DATABASE_URL == settings2.DATABASE_URL
        assert settings1.REDIS_URL == settings2.REDIS_URL
        assert settings1.page_size_default == settings2.page_size_default

class TestSettingsValidation:
    """Pruebas de validación de configuración."""

    @pytest.mark.unit
    def test_validacion_tipos_datos(self):
        """Prueba validación de tipos de datos."""
        with patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://test@localhost/test',
            'REDIS_URL': 'redis://localhost:6379/0',
            'PAGE_SIZE_DEFAULT': '25',
            'PAGE_SIZE_MAX': '100'
        }):
            # Act
            settings = Settings()
            
            # Assert - Verificar tipos
            assert isinstance(settings.DATABASE_URL, str)
            assert isinstance(settings.REDIS_URL, str) 
            assert isinstance(settings.page_size_default, int)
            assert isinstance(settings.page_size_max, int)
            assert isinstance(settings.api_prefix, str)

    @pytest.mark.unit
    def test_configuracion_con_datos_faker(self):
        """Prueba configuración con datos generados por Faker."""
        # Arrange
        fake_db_host = fake.domain_name()
        fake_db_name = fake.word()
        fake_user = fake.user_name()
        fake_password = fake.password()
        
        config_faker = {
            'DATABASE_URL': f'postgresql://{fake_user}:{fake_password}@{fake_db_host}:5432/{fake_db_name}',
            'REDIS_URL': f'redis://{fake.ipv4()}:{fake.random_int(min=6000, max=7000)}/0',
            'PAGE_SIZE_DEFAULT': str(fake.random_int(min=10, max=50)),
            'PAGE_SIZE_MAX': str(fake.random_int(min=100, max=500))
        }
        
        with patch.dict(os.environ, config_faker):
            # Act
            settings = Settings()
            
            # Assert
            assert fake_db_host in settings.DATABASE_URL
            assert fake_db_name in settings.DATABASE_URL
            assert fake_user in settings.DATABASE_URL
            assert settings.page_size_default >= 10
            assert settings.page_size_max >= 100