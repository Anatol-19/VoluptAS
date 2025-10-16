"""
Таб: Матрица трассировок/покрытия

Показывает покрытие функциональных элементов:
- Автотестами
- Тест-кейсами
- Документацией
- Багами
- Типами проверок (Smoke/Regression/Dev-only)
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QPushButton, QCheckBox, QComboBox, QTableWidget
)
from PyQt6.QtCore import Qt


class CoverageMatrixTabWidget(QWidget):
    """Таб с матрицей трассировок"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)
        
        # Панель выбора типов трассировки
        traceability_panel = QGroupBox("🎯 Что трассируем:")
        trace_layout = QHBoxLayout(traceability_panel)
        trace_layout.addWidget(QCheckBox("Автотесты"))
        trace_layout.addWidget(QCheckBox("ТЗ (Requirements)"))
        trace_layout.addWidget(QCheckBox("Тест-кейсы"))
        trace_layout.addWidget(QCheckBox("Баги"))
        trace_layout.addWidget(QCheckBox("Документация"))
        trace_layout.addStretch()
        
        layout.addWidget(traceability_panel)
        
        # Типы проверок
        check_types_panel = QGroupBox("🔥 Типы проверок:")
        check_layout = QHBoxLayout(check_types_panel)
        check_layout.addWidget(QCheckBox("Smoke"))
        check_layout.addWidget(QCheckBox("Regression"))
        check_layout.addWidget(QCheckBox("Dev-only"))
        check_layout.addStretch()
        
        layout.addWidget(check_types_panel)
        
        # Фильтры
        filters = QHBoxLayout()
        filters.addWidget(QLabel("Module:"))
        filters.addWidget(QComboBox())
        filters.addWidget(QLabel("Epic:"))
        filters.addWidget(QComboBox())
        filters.addWidget(QLabel("Feature:"))
        filters.addWidget(QComboBox())
        filters.addWidget(QCheckBox("Crit"))
        filters.addWidget(QCheckBox("Focus"))
        filters.addWidget(QCheckBox("Показать только без покрытия"))
        filters.addStretch()
        
        layout.addLayout(filters)
        
        # Таблица трассировки
        table = QTableWidget()
        table.setColumnCount(11)
        table.setHorizontalHeaderLabels([
            "FuncID", "Автотесты", "ТЗ", "Кейсы", "Smoke", "Regr",
            "Dev", "Баги", "Доки", "Coverage %", "Status"
        ])
        layout.addWidget(table, 1)
        
        # Метрики внизу
        metrics = self._create_metrics_panel()
        layout.addWidget(metrics)
        
        # Действия
        actions = QHBoxLayout()
        actions.addWidget(QPushButton("💾 Экспорт в Excel/CSV"))
        actions.addWidget(QPushButton("📊 Отчёт по покрытию (PDF)"))
        actions.addWidget(QPushButton("🔄 Обновить статусы"))
        actions.addStretch()
        
        layout.addLayout(actions)
    
    def _create_metrics_panel(self) -> QWidget:
        """Создание панели с метриками"""
        panel = QGroupBox("📈 МЕТРИКИ ПОКРЫТИЯ")
        layout = QHBoxLayout(panel)
        
        # Блок 1: Общее
        col1 = QVBoxLayout()
        col1.addWidget(QLabel("<b>Общее</b>"))
        col1.addWidget(QLabel("Всего: 156"))
        col1.addWidget(QLabel("Критических: 45"))
        col1.addWidget(QLabel("В фокусе: 23"))
        layout.addLayout(col1)
        
        # Блок 2: Автотесты
        col2 = QVBoxLayout()
        col2.addWidget(QLabel("<b>Автотесты</b>"))
        col2.addWidget(QLabel("С авто: 87 (56%)"))
        col2.addWidget(QLabel("Без авто: 69"))
        col2.addWidget(QLabel("Progress: 12"))
        layout.addLayout(col2)
        
        # Блок 3: Тест-кейсы
        col3 = QVBoxLayout()
        col3.addWidget(QLabel("<b>Тест-кейсы</b>"))
        col3.addWidget(QLabel("С кейсами: 120"))
        col3.addWidget(QLabel("Без кейсов: 36"))
        col3.addWidget(QLabel("В работе: 15"))
        layout.addLayout(col3)
        
        # Блок 4: Риски
        col4 = QVBoxLayout()
        col4.addWidget(QLabel("<b>Риски</b>"))
        col4.addWidget(QLabel("NG: 23 (15%)"))
        col4.addWidget(QLabel("OK: 98 (63%)"))
        col4.addWidget(QLabel("⚠️: 35 (22%)"))
        layout.addLayout(col4)
        
        return panel
    
    def refresh(self):
        """Обновление данных"""
        pass
