"""
Import Dialogs

Диалоги импорта данных
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
from src.services.GoogleSheetsImporter import GoogleSheetsImporter
from src.db import SessionLocal
from src.config import Config


class ImportFromCsvDialog(QDialog):
    """Диалог импорта из CSV"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Импорт из CSV")
        self.setMinimumWidth(400)
        self.file_path = None
        self.init_ui()

    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)

        # Выбор файла
        self.select_btn = QPushButton("Выбрать CSV файл...")
        self.select_btn.clicked.connect(self.select_file)
        layout.addWidget(self.select_btn)

        # Имя файла
        self.file_label = QLabel("Файл не выбран")
        layout.addWidget(self.file_label)

        # Прогресс
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        # Импорт
        self.import_btn = QPushButton("Импортировать")
        self.import_btn.clicked.connect(self.start_import)
        self.import_btn.setEnabled(False)
        layout.addWidget(self.import_btn)

    def select_file(self):
        """Выбор CSV файла"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите CSV файл", "", "CSV files (*.csv);;All Files (*)"
        )
        if file_path:
            self.file_path = file_path
            self.file_label.setText(file_path)
            self.import_btn.setEnabled(True)

    def start_import(self):
        """Начать импорт"""
        if not self.file_path:
            return

        self.progress.setVisible(True)
        self.progress.setValue(0)

        try:
            session = SessionLocal()
            importer = GoogleSheetsImporter(
                Config.get_credentials_path("google_credentials.json"), session
            )

            # Импортируем данные
            importer.import_from_csv(self.file_path)
            session.commit()

            QMessageBox.information(
                self, "Импорт завершен", "Данные успешно импортированы"
            )
            self.accept()

        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка импорта", f"Произошла ошибка при импорте: {str(e)}"
            )

        finally:
            session.close()
            self.progress.setVisible(False)
