"""
Export Dialogs

Диалоги экспорта данных
"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFileDialog,
    QPushButton,
    QLabel,
    QProgressBar,
    QMessageBox,
)


class ExportToCsvDialog(QDialog):
    """Диалог экспорта в CSV"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Экспорт в CSV")
        self.setMinimumWidth(400)
        self.init_ui()

    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)

        # Путь сохранения
        self.select_btn = QPushButton("Выбрать путь сохранения...")
        self.select_btn.clicked.connect(self.select_path)
        layout.addWidget(self.select_btn)

        # Путь
        self.path_label = QLabel("Путь не выбран")
        layout.addWidget(self.path_label)

        # Прогресс
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        # Экспорт
        self.export_btn = QPushButton("Экспортировать")
        self.export_btn.clicked.connect(self.start_export)
        self.export_btn.setEnabled(False)
        layout.addWidget(self.export_btn)

    def select_path(self):
        """Выбор пути сохранения"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить как", "", "CSV files (*.csv);;All Files (*)"
        )
        if file_path:
            self.path_label.setText(file_path)
            self.export_btn.setEnabled(True)

    def start_export(self):
        """Начать экспорт"""
        # TODO: Реализовать экспорт
        QMessageBox.information(
            self, "Экспорт", "Экспорт будет реализован в следующей версии"
        )
