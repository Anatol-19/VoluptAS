"""
Qase.io API Client - Интеграция с системой управления тест-кейсами

Возможности:
- Импорт тест-кейсов из Qase.io
- Экспорт результатов тестирования
- Синхронизация данных
- Управление Test Runs
"""

import requests
import os
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict, Optional


class QaseClient:
    """Клиент для работы с Qase.io API"""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Инициализация клиента Qase.io

        Args:
            config_path: Путь к файлу с настройками (по умолчанию credentials/qase.env)
        """
        if config_path is None:
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            config_path = project_root / "credentials" / "qase.env"

        load_dotenv(config_path)

        self.api_token = os.getenv("QASE_API_TOKEN")
        self.project_code = os.getenv("QASE_PROJECT_CODE")
        self.base_url = os.getenv("QASE_BASE_URL", "https://api.qase.io/v1")

        if not self.api_token or not self.project_code:
            raise ValueError(
                "Отсутствуют обязательные настройки Qase.io!\n"
                "Настройте API Token и Project Code в Настройках → Qase.io"
            )

        self.session = requests.Session()
        self.session.headers.update(
            {"Token": self.api_token, "Content-Type": "application/json"}
        )

    def test_connection(self) -> Dict:
        """
        Проверка подключения к Qase.io

        Returns:
            Информация о проекте
        """
        url = f"{self.base_url}/project/{self.project_code}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json().get("result", {})

    def get_all_cases(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Получить все тест-кейсы проекта

        Args:
            limit: Количество кейсов на страницу (макс 100)
            offset: Смещение для пагинации

        Returns:
            Список тест-кейсов
        """
        url = f"{self.base_url}/case/{self.project_code}"
        params = {"limit": limit, "offset": offset}

        response = self.session.get(url, params=params)
        response.raise_for_status()

        result = response.json().get("result", {})
        cases = result.get("entities", [])

        # Рекурсивно получаем все кейсы (пагинация)
        total = result.get("total", 0)
        if offset + limit < total:
            cases.extend(self.get_all_cases(limit=limit, offset=offset + limit))

        return cases

    def get_case_by_id(self, case_id: int) -> Dict:
        """
        Получить тест-кейс по ID

        Args:
            case_id: ID тест-кейса

        Returns:
            Данные тест-кейса
        """
        url = f"{self.base_url}/case/{self.project_code}/{case_id}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json().get("result", {})

    def search_cases(self, filters: Dict) -> List[Dict]:
        """
        Поиск тест-кейсов по фильтрам

        Args:
            filters: Фильтры поиска (suite_id, severity, priority, type, etc.)

        Returns:
            Список найденных тест-кейсов
        """
        url = f"{self.base_url}/case/{self.project_code}"
        response = self.session.get(url, params=filters)
        response.raise_for_status()
        return response.json().get("result", {}).get("entities", [])

    def create_case(self, case_data: Dict) -> Dict:
        """
        Создать новый тест-кейс

        Args:
            case_data: Данные кейса (title, description, severity, etc.)

        Returns:
            Созданный тест-кейс
        """
        url = f"{self.base_url}/case/{self.project_code}"
        response = self.session.post(url, json=case_data)
        response.raise_for_status()
        return response.json().get("result", {})

    def update_case(self, case_id: int, case_data: Dict) -> Dict:
        """
        Обновить тест-кейс

        Args:
            case_id: ID тест-кейса
            case_data: Обновлённые данные

        Returns:
            Обновлённый тест-кейс
        """
        url = f"{self.base_url}/case/{self.project_code}/{case_id}"
        response = self.session.patch(url, json=case_data)
        response.raise_for_status()
        return response.json().get("result", {})

    def delete_case(self, case_id: int) -> bool:
        """
        Удалить тест-кейс

        Args:
            case_id: ID тест-кейса

        Returns:
            True если успешно
        """
        url = f"{self.base_url}/case/{self.project_code}/{case_id}"
        response = self.session.delete(url)
        response.raise_for_status()
        return True

    # === TEST RUNS ===

    def get_runs(self, limit: int = 10) -> List[Dict]:
        """
        Получить список Test Runs

        Args:
            limit: Количество на страницу

        Returns:
            Список Test Runs
        """
        url = f"{self.base_url}/run/{self.project_code}"
        params = {"limit": limit}
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json().get("result", {}).get("entities", [])

    def create_run(self, run_data: Dict) -> Dict:
        """
        Создать новый Test Run

        Args:
            run_data: Данные run (title, description, cases, etc.)

        Returns:
            Созданный Test Run
        """
        url = f"{self.base_url}/run/{self.project_code}"
        response = self.session.post(url, json=run_data)
        response.raise_for_status()
        return response.json().get("result", {})

    def get_run(self, run_id: int) -> Dict:
        """
        Получить Test Run по ID

        Args:
            run_id: ID Test Run

        Returns:
            Данные Test Run
        """
        url = f"{self.base_url}/run/{self.project_code}/{run_id}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json().get("result", {})

    def complete_run(self, run_id: int) -> Dict:
        """
        Завершить Test Run

        Args:
            run_id: ID Test Run

        Returns:
            Обновлённый Test Run
        """
        url = f"{self.base_url}/run/{self.project_code}/{run_id}/complete"
        response = self.session.post(url)
        response.raise_for_status()
        return response.json().get("result", {})

    # === RESULTS ===

    def create_result(
        self,
        run_id: int,
        case_id: int,
        status: str,
        time_ms: Optional[int] = None,
        comment: Optional[str] = None,
        attachments: Optional[List[str]] = None,
    ) -> Dict:
        """
        Добавить результат выполнения тест-кейса

        Args:
            run_id: ID Test Run
            case_id: ID тест-кейса
            status: Статус (passed, failed, blocked, skipped, invalid)
            time_ms: Время выполнения в миллисекундах
            comment: Комментарий
            attachments: Список URL вложений

        Returns:
            Созданный результат
        """
        url = f"{self.base_url}/result/{self.project_code}/{run_id}"

        data = {"case_id": case_id, "status": status}

        if time_ms:
            data["time_ms"] = time_ms
        if comment:
            data["comment"] = comment
        if attachments:
            data["attachments"] = attachments

        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json().get("result", {})

    def bulk_create_results(self, run_id: int, results: List[Dict]) -> Dict:
        """
        Массовое добавление результатов

        Args:
            run_id: ID Test Run
            results: Список результатов

        Returns:
            Информация о созданных результатах
        """
        url = f"{self.base_url}/result/{self.project_code}/{run_id}/bulk"
        data = {"results": results}
        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json().get("result", {})

    # === SUITES ===

    def get_suites(self) -> List[Dict]:
        """
        Получить список тест-сьютов

        Returns:
            Список сьютов
        """
        url = f"{self.base_url}/suite/{self.project_code}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json().get("result", {}).get("entities", [])

    def create_suite(
        self,
        title: str,
        description: Optional[str] = None,
        parent_id: Optional[int] = None,
    ) -> Dict:
        """
        Создать новый сьют

        Args:
            title: Название
            description: Описание
            parent_id: ID родительского сьюта

        Returns:
            Созданный сьют
        """
        url = f"{self.base_url}/suite/{self.project_code}"
        data = {"title": title}

        if description:
            data["description"] = description
        if parent_id:
            data["parent_id"] = parent_id

        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json().get("result", {})

    # === PLANS ===

    def get_plans(self) -> List[Dict]:
        """
        Получить список Test Plans

        Returns:
            Список планов
        """
        url = f"{self.base_url}/plan/{self.project_code}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json().get("result", {}).get("entities", [])

    def create_plan(self, plan_data: Dict) -> Dict:
        """
        Создать Test Plan

        Args:
            plan_data: Данные плана (title, description, cases)

        Returns:
            Созданный план
        """
        url = f"{self.base_url}/plan/{self.project_code}"
        response = self.session.post(url, json=plan_data)
        response.raise_for_status()
        return response.json().get("result", {})

    # === SHARED STEPS ===

    def get_shared_steps(self) -> List[Dict]:
        """
        Получить список Shared Steps

        Returns:
            Список общих шагов
        """
        url = f"{self.base_url}/shared_step/{self.project_code}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json().get("result", {}).get("entities", [])

    # === ATTACHMENTS ===

    def upload_attachment(self, file_path: Path) -> List[str]:
        """
        Загрузить файл как attachment

        Args:
            file_path: Путь к файлу

        Returns:
            Список URL загруженных файлов
        """
        url = f"{self.base_url}/attachment/{self.project_code}"

        with open(file_path, "rb") as f:
            files = {"file": f}
            response = self.session.post(url, files=files)
            response.raise_for_status()

        return response.json().get("result", [])

    # === CUSTOM FIELDS ===

    def get_custom_fields(self) -> List[Dict]:
        """
        Получить список кастомных полей проекта

        Returns:
            Список кастомных полей
        """
        url = f"{self.base_url}/custom_field/{self.project_code}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json().get("result", {}).get("entities", [])


# === HELPER FUNCTIONS ===


def map_severity_to_qase(voluptas_crit: bool) -> int:
    """
    Маппинг критичности VoluptAS → Qase severity

    Args:
        voluptas_crit: is_crit из VoluptAS

    Returns:
        Qase severity ID (1-5)
    """
    # 1 = trivial, 2 = minor, 3 = normal, 4 = major, 5 = critical
    return 5 if voluptas_crit else 3


def map_qase_status_to_display(status: str) -> str:
    """
    Маппинг статуса Qase → отображение

    Args:
        status: Статус из Qase

    Returns:
        Читаемое название
    """
    mapping = {
        "passed": "✅ Пройден",
        "failed": "❌ Провален",
        "blocked": "🚫 Заблокирован",
        "skipped": "⏭️ Пропущен",
        "invalid": "⚠️ Невалидный",
    }
    return mapping.get(status, status)


def create_case_from_functional_item(item) -> Dict:
    """
    Создать структуру тест-кейса для Qase из FunctionalItem

    Args:
        item: FunctionalItem из VoluptAS

    Returns:
        Данные для создания кейса в Qase
    """
    return {
        "title": item.title or item.functional_id,
        "description": item.description or "",
        "severity": map_severity_to_qase(item.is_crit),
        "priority": 2 if item.is_focus else 1,  # 1=low, 2=medium, 3=high
        "type": 1,  # 1=other, можно расширить маппинг
        "automation": (
            2 if item.automation_status == "Automated" else 0
        ),  # 0=not automated, 1=to be automated, 2=automated
        "custom_fields": {
            "functional_id": item.functional_id,
            "module": item.module or "",
            "epic": item.epic or "",
            "feature": item.feature or "",
        },
    }
