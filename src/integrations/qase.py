"""
Qase.io Integration Client

Для управления тест-кейсами через Qase API.
API Docs: https://developers.qase.io/
"""

import logging
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class QaseClient:
    """Клиент для работы с Qase.io API"""

    def __init__(self, api_token: str, project_code: str):
        """
        Инициализация клиента Qase

        Args:
            api_token: API токен из Qase (Settings → API Tokens)
            project_code: Код проекта в Qase (например: "SAN")

        Raises:
            ValueError: Если токен или код проекта пусты
        """
        if not api_token or not project_code:
            raise ValueError("API token и project code обязательны")

        self.api_token = api_token
        self.project_code = project_code
        self.base_url = "https://api.qase.io/v1"
        self.headers = {"Token": self.api_token, "Content-Type": "application/json"}

        # Кэш для ответов (TTL: 1 час)
        self._cache = {}
        self._cache_ttl = 3600  # секунды

        logger.info(f"QaseClient инициализирован для проекта: {project_code}")

    def _get_cached(self, key: str) -> Optional[any]:
        """Получить значение из кэша если оно ещё актуально"""
        if key in self._cache:
            value, timestamp = self._cache[key]
            if datetime.now().timestamp() - timestamp < self._cache_ttl:
                logger.debug(f"Cache hit: {key}")
                return value
            else:
                del self._cache[key]
                logger.debug(f"Cache expired: {key}")
        return None

    def _set_cache(self, key: str, value: any):
        """Установить значение в кэш"""
        self._cache[key] = (value, datetime.now().timestamp())
        logger.debug(f"Cache set: {key}")

    def get_projects(self) -> List[Dict]:
        """
        Получить список всех проектов

        Returns:
            List[Dict]: Список проектов с полями [id, code, title, ...]

        Raises:
            requests.HTTPError: При ошибке API
        """
        try:
            cache_key = "projects"
            cached = self._get_cached(cache_key)
            if cached:
                return cached

            response = requests.get(
                f"{self.base_url}/project", headers=self.headers, timeout=10
            )
            response.raise_for_status()

            projects = response.json().get("result", [])
            self._set_cache(cache_key, projects)

            logger.info(f"Получено {len(projects)} проектов из Qase")
            return projects

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при получении проектов: {e}")
            raise

    def get_suites(self, project_code: Optional[str] = None) -> List[Dict]:
        """
        Получить список тест-сюит проекта

        Args:
            project_code: Код проекта (если None, используется self.project_code)

        Returns:
            List[Dict]: Список сюит с полями [id, title, ...]

        Raises:
            requests.HTTPError: При ошибке API
        """
        project_code = project_code or self.project_code

        try:
            cache_key = f"suites_{project_code}"
            cached = self._get_cached(cache_key)
            if cached:
                return cached

            response = requests.get(
                f"{self.base_url}/suite/{project_code}",
                headers=self.headers,
                timeout=10,
            )
            response.raise_for_status()

            suites = response.json().get("result", [])
            self._set_cache(cache_key, suites)

            logger.info(f"Получено {len(suites)} сюит из проекта {project_code}")
            return suites

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при получении сюит: {e}")
            raise

    def get_cases(
        self, project_code: Optional[str] = None, suite_id: Optional[int] = None
    ) -> List[Dict]:
        """
        Получить список тест-кейсов

        Args:
            project_code: Код проекта (если None, используется self.project_code)
            suite_id: Фильтр по ID сюиты (опционально)

        Returns:
            List[Dict]: Список кейсов с полями [id, title, suite_id, ...]

        Raises:
            requests.HTTPError: При ошибке API
        """
        project_code = project_code or self.project_code

        try:
            params = {}
            if suite_id:
                params["suite_id"] = suite_id

            cache_key = f"cases_{project_code}_{suite_id}"
            cached = self._get_cached(cache_key)
            if cached:
                return cached

            response = requests.get(
                f"{self.base_url}/case/{project_code}",
                headers=self.headers,
                params=params,
                timeout=10,
            )
            response.raise_for_status()

            cases = response.json().get("result", [])
            self._set_cache(cache_key, cases)

            suite_filter = f" (suite: {suite_id})" if suite_id else ""
            logger.info(f"Получено {len(cases)} кейсов из {project_code}{suite_filter}")
            return cases

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при получении кейсов: {e}")
            raise

    def create_case(
        self,
        title: str,
        project_code: Optional[str] = None,
        suite_id: Optional[int] = None,
        **kwargs,
    ) -> Dict:
        """
        Создать новый тест-кейс

        Args:
            title: Название кейса
            project_code: Код проекта (если None, используется self.project_code)
            suite_id: ID сюиты (опционально)
            **kwargs: Дополнительные параметры (description, preconditions и т.д.)

        Returns:
            Dict: Данные созданного кейса

        Raises:
            requests.HTTPError: При ошибке API
        """
        project_code = project_code or self.project_code

        try:
            data = {"title": title}
            if suite_id:
                data["suite_id"] = suite_id
            data.update(kwargs)

            response = requests.post(
                f"{self.base_url}/case/{project_code}",
                headers=self.headers,
                json=data,
                timeout=10,
            )
            response.raise_for_status()

            result = response.json().get("result", {})
            logger.info(f"Создан кейс: {title} (ID: {result.get('id')})")
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при создании кейса: {e}")
            raise

    def update_case(
        self, case_id: int, project_code: Optional[str] = None, **kwargs
    ) -> Dict:
        """
        Обновить тест-кейс

        Args:
            case_id: ID кейса
            project_code: Код проекта (если None, используется self.project_code)
            **kwargs: Поля для обновления (title, description и т.д.)

        Returns:
            Dict: Обновленные данные кейса

        Raises:
            requests.HTTPError: При ошибке API
        """
        project_code = project_code or self.project_code

        try:
            response = requests.patch(
                f"{self.base_url}/case/{project_code}/{case_id}",
                headers=self.headers,
                json=kwargs,
                timeout=10,
            )
            response.raise_for_status()

            result = response.json().get("result", {})
            logger.info(f"Обновлен кейс ID: {case_id}")
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при обновлении кейса: {e}")
            raise

    def delete_case(self, case_id: int, project_code: Optional[str] = None) -> bool:
        """
        Удалить тест-кейс

        Args:
            case_id: ID кейса
            project_code: Код проекта (если None, используется self.project_code)

        Returns:
            bool: True если успешно удалено

        Raises:
            requests.HTTPError: При ошибке API
        """
        project_code = project_code or self.project_code

        try:
            response = requests.delete(
                f"{self.base_url}/case/{project_code}/{case_id}",
                headers=self.headers,
                timeout=10,
            )
            response.raise_for_status()

            logger.info(f"Удален кейс ID: {case_id}")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при удалении кейса: {e}")
            raise

    def check_connection(self) -> bool:
        """
        Проверить подключение к Qase API

        Returns:
            bool: True если подключение успешно
        """
        try:
            response = requests.get(
                f"{self.base_url}/project", headers=self.headers, timeout=5
            )
            if response.status_code == 200:
                logger.info("✅ Qase API подключение успешно")
                return True
            else:
                logger.warning(f"⚠️ Qase API ошибка: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к Qase: {e}")
            return False
