"""
Project Dialogs

Диалоги управления проектами
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton,
    QLabel, QListWidget, QMessageBox,
    QInputDialog
)
from src.config import Config


class ProjectManagerDialog(QDialog):
    """Диалог управления проектами"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Управление проектами")
        self.setMinimumWidth(500)
        self.init_ui()

    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)

        # Текущий проект
        current_label = QLabel(f"Текущий проект: {Config.CURRENT_PROJECT}")
        layout.addWidget(current_label)

        # Список проектов
        self.list_widget = QListWidget()
        self.refresh_projects()
        layout.addWidget(self.list_widget)

        # Кнопки управления
        btn_new = QPushButton("Создать проект")
        btn_new.clicked.connect(self.create_project)
        layout.addWidget(btn_new)

        btn_switch = QPushButton("Переключить")
        btn_switch.clicked.connect(self.switch_project)
        layout.addWidget(btn_switch)

        btn_delete = QPushButton("Удалить")
        btn_delete.clicked.connect(self.delete_project)
        layout.addWidget(btn_delete)

    def refresh_projects(self):
        """Обновление списка проектов"""
        self.list_widget.clear()
        self.list_widget.addItems(Config.get_projects_list())

        # Выделяем текущий проект
        for i in range(self.list_widget.count()):
            if self.list_widget.item(i).text() == Config.CURRENT_PROJECT:
                self.list_widget.setCurrentRow(i)
                break

    def create_project(self):
        """Создание нового проекта"""
        name, ok = QInputDialog.getText(
            self,
            "Новый проект",
            "Введите имя проекта:"
        )
        if ok and name:
            if Config.create_project(name):
                QMessageBox.information(
                    self,
                    "Создание проекта",
                    f"Проект {name} успешно создан"
                )
                self.refresh_projects()
            else:
                QMessageBox.warning(
                    self,
                    "Ошибка создания проекта",
                    f"Проект {name} уже существует или произошла ошибка"
                )

    def switch_project(self):
        """Переключение проекта"""
        if not self.list_widget.currentItem():
            QMessageBox.warning(
                self,
                "Переключение проекта",
                "Выберите проект для переключения"
            )
            return

        project = self.list_widget.currentItem().text()
        if Config.switch_project(project):
            QMessageBox.information(
                self,
                "Переключение проекта",
                f"Проект успешно переключен на {project}"
            )
            self.refresh_projects()
            self.accept()  # Закрываем диалог
        else:
            QMessageBox.warning(
                self,
                "Ошибка переключения",
                f"Не удалось переключиться на проект {project}"
            )

    def delete_project(self):
        """Удаление проекта"""
        if not self.list_widget.currentItem():
            QMessageBox.warning(
                self,
                "Удаление проекта",
                "Выберите проект для удаления"
            )
            return

        project = self.list_widget.currentItem().text()
        if project == "default":
            QMessageBox.warning(
                self,
                "Удаление проекта",
                "Нельзя удалить проект по умолчанию"
            )
            return

        reply = QMessageBox.question(
            self,
            "Удаление проекта",
            f"Вы уверены, что хотите удалить проект {project}?\nЭто действие нельзя отменить!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if Config.delete_project(project):
                QMessageBox.information(
                    self,
                    "Удаление проекта",
                    f"Проект {project} успешно удален"
                )
                self.refresh_projects()
            else:
                QMessageBox.warning(
                    self,
                    "Ошибка удаления",
                    f"Не удалось удалить проект {project}"
                )
