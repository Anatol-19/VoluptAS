"""
Генератор BDD Feature файлов из FunctionalItem
"""

from pathlib import Path
from src.models import FunctionalItem


class FeatureGenerator:
    """Генератор Gherkin feature файлов"""

    @staticmethod
    def generate_feature(item: FunctionalItem) -> str:
        """
        Генерация feature файла для элемента

        Args:
            item: FunctionalItem для которого генерируется feature

        Returns:
            str: Содержимое feature файла в формате Gherkin
        """
        # Теги
        tags = []
        if item.is_crit:
            tags.append("@critical")
        if item.is_focus:
            tags.append("@focus")
        if item.segment:
            tags.append(f'@{item.segment.lower().replace("/", "_")}')
        if item.type:
            tags.append(f"@{item.type.lower()}")

        tag_line = " ".join(tags) if tags else ""

        # Feature название
        feature_name = item.title or item.functional_id

        # Description
        description = (
            item.description
            or f"Автоматически сгенерированная feature для {item.functional_id}"
        )

        # Background (если есть зависимости)
        background = ""
        if item.module or item.epic:
            background_steps = []
            if item.module:
                background_steps.append(f'    Given модуль "{item.module}" доступен')
            if item.epic:
                background_steps.append(f'    And эпик "{item.epic}" инициализирован')

            if background_steps:
                background = "\n  Background:\n" + "\n".join(background_steps) + "\n"

        # Scenarios (базовые)
        scenarios = []

        # Scenario 1: Базовая функциональность
        scenarios.append(f"""
  Scenario: Базовая функциональность {feature_name}
    Given пользователь авторизован
    When пользователь использует "{feature_name}"
    Then функционал работает корректно
    And нет ошибок""")

        # Scenario 2: Для критичных - негативный тест
        if item.is_crit:
            scenarios.append(f"""
  @negative
  Scenario: Обработка ошибок {feature_name}
    Given пользователь авторизован
    When происходит ошибка в "{feature_name}"
    Then система обрабатывает ошибку корректно
    And пользователь получает информативное сообщение""")

        # Собираем всё вместе
        feature_content = f"""{tag_line}
Feature: {feature_name}
  
  {description}
  
  Functional ID: {item.functional_id}
  Module: {item.module or 'N/A'}
  Epic: {item.epic or 'N/A'}
  Responsible QA: {item.responsible_qa.name if item.responsible_qa else 'N/A'}
  Responsible Dev: {item.responsible_dev.name if item.responsible_dev else 'N/A'}
{background}
{"".join(scenarios)}
"""

        return feature_content

    @staticmethod
    def save_feature(item: FunctionalItem, output_dir: Path) -> Path:
        """
        Сохранить feature файл на диск

        Args:
            item: FunctionalItem
            output_dir: Директория для сохранения

        Returns:
            Path: Путь к сохранённому файлу
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Имя файла из functional_id
        filename = f"{item.functional_id.replace('.', '_')}.feature"
        filepath = output_dir / filename

        content = FeatureGenerator.generate_feature(item)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return filepath

    @staticmethod
    def batch_generate(items: list, output_dir: Path) -> list:
        """
        Массовая генерация feature файлов

        Args:
            items: Список FunctionalItem
            output_dir: Директория для сохранения

        Returns:
            list: Список путей к сохранённым файлам
        """
        saved_files = []

        for item in items:
            try:
                filepath = FeatureGenerator.save_feature(item, output_dir)
                saved_files.append(filepath)
            except Exception as e:
                print(f"Ошибка генерации feature для {item.functional_id}: {e}")

        return saved_files
