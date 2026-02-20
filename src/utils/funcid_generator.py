"""
FuncID Generator

Автоматическая генерация уникальных идентификаторов на основе иерархии.

Формат:
- Module: MOD:{ALIAS}
- Epic: EPIC:{MODULE}.{ALIAS}
- Feature: FEAT:{MODULE}.{EPIC}.{ALIAS}
- Story: STORY:{MODULE}.{EPIC}.{FEATURE}.{ALIAS}
- Page: PAGE:{MODULE}.{EPIC}.{FEATURE}.{ALIAS}
- Element: ELEM:{MODULE}.{EPIC}.{FEATURE}.{PAGE}.{ALIAS}
- Service: SVC:{ALIAS}

Примеры:
- MOD:FRONT
- EPIC:FRONT.AUTH
- FEAT:FRONT.AUTH.LOGIN
- STORY:FRONT.AUTH.LOGIN.SOCIAL
"""

import re
from typing import Optional
from src.models import FunctionalItem


def normalize_alias(text: str) -> str:
    """
    Нормализация текста для использования в FuncID
    
    Правила:
    - Транслитерация (опционально)
    - Удаление спецсимволов
    - Замена пробелов на _
    - Upper case
    
    Пример:
    "User Authentication" → "USER_AUTHENTICATION"
    "Авторизация" → "AVTORIZATSIYA"
    """
    if not text:
        return ""
    
    # Удаляем спецсимволы, оставляем буквы, цифры, пробелы
    text = re.sub(r'[^\w\s-]', '', text)
    
    # Заменяем пробелы и дефисы на подчёркивание
    text = re.sub(r'[\s-]+', '_', text)
    
    # Upper case
    text = text.upper()
    
    # Обрезаем до 20 символов
    return text[:20]


def generate_funcid(
    item_type: str,
    title: str,
    module: Optional[str] = None,
    epic: Optional[str] = None,
    feature: Optional[str] = None,
    parent_item: Optional[FunctionalItem] = None
) -> str:
    """
    Генерация FuncID на основе иерархии
    
    Args:
        item_type: Тип элемента (Module, Epic, Feature, Story, Page, Element, Service)
        title: Название элемента
        module: Название модуля (опционально)
        epic: Название эпика (опционально)
        feature: Название фичи (опционально)
        parent_item: Родительский элемент (опционально, приоритет над module/epic/feature)
    
    Returns:
        Сгенерированный FuncID
    
    Examples:
        >>> generate_funcid('Module', 'Frontend')
        'MOD:FRONTEND'
        
        >>> generate_funcid('Epic', 'Auth', module='FRONTEND')
        'EPIC:FRONTEND.AUTH'
        
        >>> generate_funcid('Feature', 'Login', module='FRONTEND', epic='AUTH')
        'FEAT:FRONTEND.AUTH.LOGIN'
    """
    # Нормализуем название текущего элемента
    alias = normalize_alias(title)
    
    # Префикс по типу
    type_prefix = {
        'Module': 'MOD',
        'Epic': 'EPIC',
        'Feature': 'FEAT',
        'Story': 'STORY',
        'Page': 'PAGE',
        'Element': 'ELEM',
        'Service': 'SVC',
    }.get(item_type, 'ITEM')
    
    # Если есть родитель — используем его FuncID как основу
    if parent_item:
        parent_funcid = parent_item.functional_id or ''
        base = parent_funcid.rstrip(':') if parent_funcid else ''
        
        # Для Story/Feature/Page добавляем alias родителя если нет в base
        if item_type in ['Story', 'Feature', 'Page', 'Element']:
            if base and alias:
                return f"{type_prefix}:{base}.{alias}"
            elif alias:
                return f"{type_prefix}:{alias}"
    
    # Собираем иерархию из отдельных полей
    parts = []
    
    if module and item_type not in ['Module', 'Service']:
        parts.append(normalize_alias(module))
    
    if epic and item_type not in ['Module', 'Epic', 'Service']:
        parts.append(normalize_alias(epic))
    
    if feature and item_type not in ['Module', 'Epic', 'Feature', 'Service']:
        parts.append(normalize_alias(feature))
    
    # Добавляем текущий alias
    if alias:
        parts.append(alias)
    
    # Формируем итоговый FuncID
    if parts:
        return f"{type_prefix}:{'.'.join(parts)}"
    
    # Fallback: только тип + alias
    return f"{type_prefix}:{alias}" if alias else f"{type_prefix}:NEW"


def suggest_children(item: FunctionalItem) -> list:
    """
    Предложение дочерних элементов на основе типа родителя
    
    Args:
        item: Родительский элемент
    
    Returns:
        Список словарей с предложениями:
        [{'type': 'Epic', 'title': '...', 'description': '...'}, ...]
    """
    suggestions = {
        'Module': [
            {'type': 'Epic', 'title': f'{item.title} Core', 'description': 'Основной функционал'},
            {'type': 'Epic', 'title': f'{item.title} Integration', 'description': 'Интеграции'},
            {'type': 'Epic', 'title': f'{item.title} UI', 'description': 'Пользовательский интерфейс'},
        ],
        'Epic': [
            {'type': 'Feature', 'title': 'CRUD Operations', 'description': 'Create, Read, Update, Delete'},
            {'type': 'Feature', 'title': 'Validation', 'description': 'Валидация данных'},
            {'type': 'Feature', 'title': 'Reports', 'description': 'Отчёты и статистика'},
        ],
        'Feature': [
            {'type': 'Story', 'title': 'Create', 'description': 'Создание элемента'},
            {'type': 'Story', 'title': 'Read', 'description': 'Просмотр элемента'},
            {'type': 'Story', 'title': 'Update', 'description': 'Редактирование элемента'},
            {'type': 'Story', 'title': 'Delete', 'description': 'Удаление элемента'},
        ],
    }
    
    return suggestions.get(item.type, [])


def validate_funcid(funcid: str, session, exclude_id: Optional[int] = None) -> bool:
    """
    Проверка уникальности FuncID
    
    Args:
        funcid: FuncID для проверки
        session: SQLAlchemy session
        exclude_id: ID элемента для исключения (при редактировании)
    
    Returns:
        True если уникален, False если дубликат
    """
    query = session.query(FunctionalItem).filter_by(functional_id=funcid)
    
    if exclude_id:
        query = query.filter(FunctionalItem.id != exclude_id)
    
    return query.first() is None


def make_unique_funcid(base_funcid: str, session, exclude_id: Optional[int] = None) -> str:
    """
    Создание уникального FuncID путём добавления суффикса
    
    Args:
        base_funcid: Базовый FuncID
        session: SQLAlchemy session
        exclude_id: ID элемента для исключения
    
    Returns:
        Уникальный FuncID
    
    Examples:
        Если STORY:FRONT.AUTH.LOGIN уже существует:
        → STORY:FRONT.AUTH.LOGIN.1
        → STORY:FRONT.AUTH.LOGIN.2
    """
    if validate_funcid(base_funcid, session, exclude_id):
        return base_funcid
    
    # Добавляем числовой суффикс
    counter = 1
    while True:
        candidate = f"{base_funcid}.{counter}"
        if validate_funcid(candidate, session, exclude_id):
            return candidate
        counter += 1
