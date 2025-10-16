"""
Таб: INFRA Maturity - Зрелость инфраструктуры

Категории:
- Code Maturity
- Container
- DB Name
- Subsystems Involved
- External Services
- Security
- Metrics
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QPushButton, QTableWidget, QProgressBar
)
from PyQt6.QtCore import Qt


class InfraMaturityTabWidget(QWidget):
    """Таб для отображения зрелости инфраструктуры"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)
        
        # Заголовок
        header = QHBoxLayout()
        header.addWidget(QLabel("<h2>🏗️ INFRA MATURITY</h2>"))
        header.addStretch()
        header.addWidget(QPushButton("✏️ Редактировать элемент INFRA"))
        header.addWidget(QPushButton("💾 Экспорт отчёта"))
        header.addWidget(QPushButton("🔄 Обновить статусы"))
        
        layout.addLayout(header)
        
        # Категории (горизонтальные табы)
        categories = QTabWidget()
        categories.setTabPosition(QTabWidget.TabPosition.North)
        
        categories.addTab(self._create_code_category(), "🎯 CODE")
        categories.addTab(self._create_container_category(), "🐳 CONTAINER")
        categories.addTab(self._create_db_category(), "🗄️ DB")
        categories.addTab(self._create_subsystems_category(), "🧩 SUBSYSTEMS")
        categories.addTab(self._create_external_category(), "🔗 EXTERNAL")
        categories.addTab(self._create_security_category(), "🔐 SECURITY")
        categories.addTab(self._create_metrics_category(), "📊 METRICS")
        
        layout.addWidget(categories, 1)
        
        # Общая метрика зрелости внизу
        overall = self._create_overall_metrics()
        layout.addWidget(overall)
    
    def _create_code_category(self) -> QWidget:
        """Создание категории Code Maturity"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("<b>🎯 CODE MATURITY</b>"))
        
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "Репозиторий", "Покрытие тестами", "Линтер", "Typecheck", "CI/CD", "Docs"
        ])
        layout.addWidget(table)
        
        return widget
    
    def _create_container_category(self) -> QWidget:
        """Создание категории Container"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("<b>🐳 CONTAINER MATURITY</b>"))
        
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "Контейнер", "Образ", "Версия", "Registry", "Health", "Auto"
        ])
        layout.addWidget(table)
        
        return widget
    
    def _create_db_category(self) -> QWidget:
        """Создание категории DB Name"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("<b>🗄️ DATABASE</b>"))
        
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "База данных", "Версия", "Бэкапы", "Миграции", "Индексы", "Мониторинг"
        ])
        layout.addWidget(table)
        
        return widget
    
    def _create_subsystems_category(self) -> QWidget:
        """Создание категории Subsystems"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("<b>🧩 SUBSYSTEMS INVOLVED</b>"))
        
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels([
            "Подсистема", "Владелец", "SLA", "Зависимости", "Критичность"
        ])
        layout.addWidget(table)
        
        return widget
    
    def _create_external_category(self) -> QWidget:
        """Создание категории External Services"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("<b>🔗 EXTERNAL SERVICES</b>"))
        
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "Внешний сервис", "Провайдер", "SLA", "Failover", "Costs/mo", "Status"
        ])
        layout.addWidget(table)
        
        return widget
    
    def _create_security_category(self) -> QWidget:
        """Создание категории Security"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("<b>🔐 SECURITY</b>"))
        layout.addWidget(QLabel("Placeholder для security metrics"))
        
        return widget
    
    def _create_metrics_category(self) -> QWidget:
        """Создание категории Metrics"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("<b>📊 METRICS</b>"))
        layout.addWidget(QLabel("Placeholder для общих метрик"))
        
        return widget
    
    def _create_overall_metrics(self) -> QWidget:
        """Создание панели общих метрик"""
        widget = QWidget()
        widget.setStyleSheet("background-color: #f0f0f0; padding: 10px;")
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("<b>📊 ОБЩИЕ МЕТРИКИ ЗРЕЛОСТИ</b>"))
        
        # Прогресс-бары для категорий
        metrics = QHBoxLayout()
        
        for category, value in [
            ("CODE", 65),
            ("CONTAINER", 80),
            ("DB", 70),
            ("SUBSYSTEMS", 75),
            ("EXTERNAL", 85),
        ]:
            col = QVBoxLayout()
            col.addWidget(QLabel(f"<b>{category}</b>"))
            progress = QProgressBar()
            progress.setValue(value)
            col.addWidget(progress)
            metrics.addLayout(col)
        
        layout.addLayout(metrics)
        
        # Общая зрелость
        overall_label = QLabel("<h3>🏆 ОБЩАЯ ЗРЕЛОСТЬ: 75% (Good)</h3>")
        overall_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(overall_label)
        
        return widget
    
    def refresh(self):
        """Обновление данных"""
        pass
