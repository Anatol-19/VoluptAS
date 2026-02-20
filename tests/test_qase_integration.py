"""
Тесты для Qase Integration

Тестирование QaseClient и синхронизации с Qase.io
"""

import pytest
from src.integrations.qase import QaseClient


class TestQaseClient:
    """Тесты QaseClient"""

    def test_init_with_valid_credentials(self):
        """Инициализация с валидными credentials"""
        client = QaseClient(api_token="test_token", project_code="TEST")
        assert client.api_token == "test_token"
        assert client.project_code == "TEST"
        assert client.base_url == "https://api.qase.io/v1"

    def test_init_with_empty_token_raises_error(self):
        """Инициализация с пустым токеном вызывает ошибку"""
        with pytest.raises(ValueError):
            QaseClient(api_token="", project_code="TEST")

    def test_init_with_empty_project_raises_error(self):
        """Инициализация с пустым project_code вызывает ошибку"""
        with pytest.raises(ValueError):
            QaseClient(api_token="token", project_code="")

    def test_cache_functionality(self):
        """Проверка работы кэша"""
        client = QaseClient(api_token="test", project_code="TEST")

        # Установить значение в кэш
        test_data = [{"id": 1, "title": "Test"}]
        client._set_cache("test_key", test_data)

        # Получить из кэша
        cached = client._get_cached("test_key")
        assert cached == test_data

        # Проверить что истёкший кэш удаляется
        client._cache["expired"] = ({"data": "old"}, 0)  # timestamp = 0 (очень старый)
        assert client._get_cached("expired") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

