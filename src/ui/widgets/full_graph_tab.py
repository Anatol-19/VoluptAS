"""
Таб: Полный граф связей

Obsidian-style граф со всеми элементами и связями
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QPushButton
from PyQt6.QtCore import Qt


class FullGraphTabWidget(QWidget):
    """Таб с полным графом связей"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)
        
        # Панель управления
        controls = QHBoxLayout()
        controls.addWidget(QLabel("<b>Типы связей:</b>"))
        controls.addWidget(QCheckBox("Иерархия"))
        controls.addWidget(QCheckBox("Функционал"))
        controls.addWidget(QCheckBox("POM"))
        controls.addWidget(QCheckBox("Service"))
        controls.addWidget(QCheckBox("Test"))
        controls.addWidget(QCheckBox("Doc"))
        controls.addStretch()
        controls.addWidget(QPushButton("🔄 Обновить"))
        controls.addWidget(QPushButton("💾 Экспорт PNG/SVG"))
        
        layout.addLayout(controls)
        
        # Placeholder для графа
        placeholder = QLabel(
            "<h2>🌐 Obsidian-style Graph View</h2>"
            "<p>Полный граф связей всех элементов</p>"
            "<hr>"
            "<p>Функционал:</p>"
            "<ul>"
            "<li>Zoom, Pan</li>"
            "<li>Фильтрация по типам связей</li>"
            "<li>Клик по узлу → информация</li>"
            "<li>Двойной клик → редактор</li>"
            "</ul>"
        )
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(placeholder, 1)
    
    def refresh(self):
        """Обновление данных"""
        pass
