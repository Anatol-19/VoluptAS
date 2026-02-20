"""
Graph Builder

Построение графа связей из атрибутов FunctionalItem.
Связи извлекаются "на лету" из:
- parent_id (явная связь)
- module, epic, feature, story, page (иерархические связи)
"""

from typing import List, Dict, Tuple, Optional
from src.models import FunctionalItem


# Цвета для типов элементов (Obsidian-style)
NODE_COLORS = {
    'Module': '#1E90FF',      # Синий
    'Epic': '#32CD32',        # Зелёный
    'Feature': '#FFA500',     # Оранжевый
    'Story': '#9370DB',       # Фиолетовый
    'Page': '#FF69B4',        # Розовый
    'Element': '#00CED1',     # Голубой
    'Service': '#DC143C',     # Красный
}

# Размеры узлов по типу
NODE_SIZES = {
    'Module': 5000,
    'Epic': 3000,
    'Feature': 2000,
    'Story': 1000,
    'Page': 1000,
    'Element': 500,
    'Service': 1500,
}


def build_graph_from_attributes(items: List[FunctionalItem]) -> Tuple[List[Dict], List[Dict]]:
    """
    Построение графа из атрибутов элементов
    
    Args:
        items: Список элементов FunctionalItem
    
    Returns:
        (nodes, edges) — списки узлов и рёбер
    """
    nodes = []
    edges = []
    
    # Индекс для быстрого поиска
    items_by_id = {item.id: item for item in items}
    items_by_title_type = {}
    for item in items:
        key = (item.title.lower(), item.type)
        items_by_title_type[key] = item
    
    # 1. Создаём узлы
    for item in items:
        nodes.append({
            'id': item.id,
            'title': item.title,
            'type': item.type,
            'funcid': item.functional_id,
            'color': NODE_COLORS.get(item.type, '#808080'),
            'size': NODE_SIZES.get(item.type, 1000),
        })
    
    # 2. Создаём рёбра из атрибутов
    for item in items:
        # parent_id — явная связь parent-of
        if item.parent_id and item.parent_id in items_by_id:
            edges.append({
                'from': item.parent_id,
                'to': item.id,
                'type': 'parent-of',
                'weight': 1.0,
            })
        
        # module — связь module-of
        if item.module:
            parent = find_parent_by_title(items, item.module, 'Module')
            if parent and parent.id != item.id:
                edges.append({
                    'from': parent.id,
                    'to': item.id,
                    'type': 'module-of',
                    'weight': 0.8,
                })
        
        # epic — связь epic-of
        if item.epic:
            parent = find_parent_by_title(items, item.epic, 'Epic')
            if parent and parent.id != item.id:
                edges.append({
                    'from': parent.id,
                    'to': item.id,
                    'type': 'epic-of',
                    'weight': 0.9,
                })
        
        # feature — связь feature-of
        if item.feature:
            parent = find_parent_by_title(items, item.feature, 'Feature')
            if parent and parent.id != item.id:
                edges.append({
                    'from': parent.id,
                    'to': item.id,
                    'type': 'feature-of',
                    'weight': 0.95,
                })
        
        # stories — JSON array или CSV, не используем для иерархии
        # page — связь page-of (если есть поле)
        if hasattr(item, 'page') and item.page:
            parent = find_parent_by_title(items, item.page, 'Page')
            if parent and parent.id != item.id:
                edges.append({
                    'from': parent.id,
                    'to': item.id,
                    'type': 'page-of',
                    'weight': 0.95,
                })
    
    return nodes, edges


def find_parent_by_title(items: List[FunctionalItem], title: str, type_filter: str) -> Optional[FunctionalItem]:
    """
    Поиск родителя по названию и типу
    
    Args:
        items: Список элементов
        title: Название для поиска
        type_filter: Тип элемента (Module, Epic, Feature...)
    
    Returns:
        Элемент или None
    """
    title_lower = title.lower()
    
    for item in items:
        if item.type == type_filter and item.title.lower() == title_lower:
            return item
    
    return None


def build_hierarchy_graph(items: List[FunctionalItem], root_type: str = 'Module') -> Tuple[List[Dict], List[Dict]]:
    """
    Построение только иерархического графа (parent-of связи)
    
    Args:
        items: Список элементов
        root_type: Корневой тип (Module, Epic...)
    
    Returns:
        (nodes, edges)
    """
    nodes = []
    edges = []
    
    items_by_id = {item.id: item for item in items}
    
    for item in items:
        nodes.append({
            'id': item.id,
            'title': item.title,
            'type': item.type,
            'funcid': item.functional_id,
            'color': NODE_COLORS.get(item.type, '#808080'),
            'size': NODE_SIZES.get(item.type, 1000),
        })
        
        if item.parent_id and item.parent_id in items_by_id:
            edges.append({
                'from': item.parent_id,
                'to': item.id,
                'type': 'parent-of',
                'weight': 1.0,
            })
    
    return nodes, edges


def get_item_neighbors(item: FunctionalItem, items: List[FunctionalItem]) -> Tuple[List[FunctionalItem], List[FunctionalItem]]:
    """
    Получение соседей элемента (родители и дети)
    
    Args:
        item: Элемент
        items: Все элементы
    
    Returns:
        (parents, children)
    """
    parents = []
    children = []
    
    # Родители
    if item.parent_id:
        parent = next((i for i in items if i.id == item.parent_id), None)
        if parent:
            parents.append(parent)
    
    if item.module:
        parent = find_parent_by_title(items, item.module, 'Module')
        if parent and parent not in parents:
            parents.append(parent)
    
    if item.epic:
        parent = find_parent_by_title(items, item.epic, 'Epic')
        if parent and parent not in parents:
            parents.append(parent)
    
    if item.feature:
        parent = find_parent_by_title(items, item.feature, 'Feature')
        if parent and parent not in parents:
            parents.append(parent)
    
    # Дети
    for i in items:
        if i.parent_id == item.id:
            children.append(i)
        elif i.module and i.module.lower() == item.title.lower() and item.type == 'Module':
            if i not in children:
                children.append(i)
        elif i.epic and i.epic.lower() == item.title.lower() and item.type == 'Epic':
            if i not in children:
                children.append(i)
        elif i.feature and i.feature.lower() == item.title.lower() and item.type == 'Feature':
            if i not in children:
                children.append(i)
    
    return parents, children
