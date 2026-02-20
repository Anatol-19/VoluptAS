"""
Tests for Graph Builder

Проверка построения графа из атрибутов и связей
"""

import pytest
from src.utils.graph_builder import (
    build_graph_from_attributes,
    find_parent_by_title,
    get_item_neighbors,
    NODE_COLORS,
    NODE_SIZES,
)
from src.models import FunctionalItem, Relation


class TestFindParentByTitle:
    """Тесты поиска родителя по названию"""

    def test_exact_match(self):
        """Точное совпадение"""
        items = [
            FunctionalItem(id=1, title="FRONTEND", type="Module"),
            FunctionalItem(id=2, title="AUTH", type="Epic"),
        ]

        parent = find_parent_by_title(items, "FRONTEND", "Module")

        assert parent is not None
        assert parent.id == 1
        assert parent.type == "Module"

    def test_match_without_prefix(self):
        """Совпадение без префикса [Module]:"""
        items = [
            FunctionalItem(id=1, title="[Module]: FRONTEND", type="Module"),
        ]

        parent = find_parent_by_title(items, "FRONTEND", "Module")

        assert parent is not None
        assert parent.id == 1

    def test_match_by_funcid(self):
        """Совпадение по functional_id"""
        items = [
            FunctionalItem(id=1, title="FRONTEND", type="Module", functional_id="MOD:FRONTEND"),
        ]

        parent = find_parent_by_title(items, "FRONTEND", "Module")

        assert parent is not None
        assert parent.id == 1

    def test_partial_match(self):
        """Частичное совпадение (contains)"""
        items = [
            FunctionalItem(id=1, title="Authentication", type="Epic"),
        ]

        # "auth" содержится в "Authentication"
        parent = find_parent_by_title(items, "Authentication", "Epic")

        assert parent is not None
        assert parent.id == 1

    def test_no_match(self):
        """Нет совпадения"""
        items = [
            FunctionalItem(id=1, title="FRONTEND", type="Module"),
            FunctionalItem(id=2, title="BACKEND", type="Module"),
        ]

        # Ищем несуществующий
        parent = find_parent_by_title(items, "NONEXISTENT", "Module")

        assert parent is None


class TestBuildGraphFromAttributes:
    """Тесты построения графа"""

    def test_build_nodes(self):
        """Построение узлов"""
        items = [
            FunctionalItem(id=1, title="FRONTEND", type="Module", functional_id="MOD:FRONT"),
            FunctionalItem(id=2, title="AUTH", type="Epic", functional_id="EPIC:AUTH"),
        ]

        nodes, edges = build_graph_from_attributes(items)

        assert len(nodes) == 2
        assert nodes[0]["id"] == 1
        assert nodes[0]["type"] == "Module"
        assert nodes[0]["color"] == NODE_COLORS["Module"]
        assert nodes[1]["id"] == 2
        assert nodes[1]["type"] == "Epic"

    def test_build_hierarchy_edges(self):
        """Построение иерархических рёбер"""
        items = [
            FunctionalItem(id=1, title="FRONTEND", type="Module"),
            FunctionalItem(id=2, title="AUTH", type="Epic", module="FRONTEND"),
        ]

        nodes, edges = build_graph_from_attributes(items)

        # Должно быть хотя бы одно ребро (module-of)
        assert len(edges) >= 1

        # Проверяем что есть ребро module-of
        module_edges = [e for e in edges if e["type"] == "module-of"]
        assert len(module_edges) >= 1

    def test_build_parent_edges(self):
        """Построение рёбер parent-of"""
        items = [
            FunctionalItem(id=1, title="FRONTEND", type="Module"),
            FunctionalItem(id=2, title="AUTH", type="Epic", parent_id=1),
        ]

        nodes, edges = build_graph_from_attributes(items)

        # Должно быть ребро parent-of
        parent_edges = [e for e in edges if e["type"] == "parent-of"]
        assert len(parent_edges) == 1
        assert parent_edges[0]["from"] == 1
        assert parent_edges[0]["to"] == 2

    def test_build_with_relations(self):
        """Построение с связями из БД"""
        items = [
            FunctionalItem(id=1, title="FRONTEND", type="Module"),
            FunctionalItem(id=2, title="AUTH", type="Epic"),
            FunctionalItem(id=3, title="LOGIN", type="Feature"),
        ]

        # Создаём mock связи
        relations = [
            Relation(
                id=1,
                source_id=2,
                target_id=3,
                type="functional",
                weight=1.0,
                active=True,
            )
        ]

        nodes, edges = build_graph_from_attributes(items, relations)

        # Проверяем что связь добавлена
        functional_edges = [e for e in edges if e["type"] == "functional"]
        assert len(functional_edges) == 1
        assert functional_edges[0]["from"] == 2
        assert functional_edges[0]["to"] == 3

    def test_inactive_relations_ignored(self):
        """Неактивные связи игнорируются"""
        items = [
            FunctionalItem(id=1, title="FRONTEND", type="Module"),
            FunctionalItem(id=2, title="AUTH", type="Epic"),
        ]

        relations = [
            Relation(
                id=1,
                source_id=1,
                target_id=2,
                type="functional",
                active=False,  # Неактивная
            )
        ]

        nodes, edges = build_graph_from_attributes(items, relations)

        # Связь не должна быть добавлена
        functional_edges = [e for e in edges if e["type"] == "functional"]
        assert len(functional_edges) == 0


class TestGetItemNeighbors:
    """Тесты получения соседей элемента"""

    def test_get_parents(self):
        """Получение родителей"""
        items = [
            FunctionalItem(id=1, title="FRONTEND", type="Module"),
            FunctionalItem(id=2, title="AUTH", type="Epic", module="FRONTEND"),
        ]

        parents, children = get_item_neighbors(items[1], items)

        assert len(parents) == 1
        assert parents[0].id == 1

    def test_get_children(self):
        """Получение детей"""
        items = [
            FunctionalItem(id=1, title="FRONTEND", type="Module"),
            FunctionalItem(id=2, title="AUTH", type="Epic", module="FRONTEND"),
        ]

        parents, children = get_item_neighbors(items[0], items)

        assert len(children) == 1
        assert children[0].id == 2

    def test_no_neighbors(self):
        """Нет соседей"""
        items = [
            FunctionalItem(id=1, title="FRONTEND", type="Module"),
        ]

        parents, children = get_item_neighbors(items[0], items)

        assert len(parents) == 0
        assert len(children) == 0
