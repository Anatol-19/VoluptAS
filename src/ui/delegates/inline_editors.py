"""
Inline Editing Delegates

Делегаты для редактирования прямо в таблице.
"""

from PyQt6.QtWidgets import QItemDelegate, QLineEdit, QComboBox, QCheckBox, QWidget
from PyQt6.QtCore import Qt


class InlineEditDelegate(QItemDelegate):
    """Базовый делегат для inline редактирования"""
    
    def __init__(self, parent=None, on_commit=None):
        super().__init__(parent)
        self.on_commit = on_commit  # Callback при сохранении
    
    def createEditor(self, parent, option, index):
        """Создание редактора"""
        editor = QLineEdit(parent)
        editor.setFrame(False)
        editor.setStyleSheet("background: white; border: 2px solid #0078d7;")
        return editor
    
    def setEditorData(self, editor, index):
        """Установка данных в редактор"""
        value = index.model().data(index, Qt.ItemDataRole.EditRole)
        editor.setText(str(value) if value else "")
    
    def setModelData(self, editor, model, index):
        """Сохранение данных в модель"""
        value = editor.text()
        model.setData(index, value, Qt.ItemDataRole.EditRole)
        
        # Callback для сохранения в БД
        if self.on_commit:
            self.on_commit(index.row(), index.column(), value)
    
    def updateEditorGeometry(self, editor, option, index):
        """Обновление геометрии редактора"""
        editor.setGeometry(option.rect)


class InlineSegmentDelegate(QItemDelegate):
    """Делегат для Segment (ComboBox)"""
    
    SEGMENTS = [
        '', 'UI', 'UX/CX', 'API', 'Backend', 'Database',
        'Integration', 'Security', 'Performance', 'Workflow', 'Mobile'
    ]
    
    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        editor.addItems(self.SEGMENTS)
        editor.setStyleSheet("background: white; border: 2px solid #0078d7;")
        return editor
    
    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.ItemDataRole.EditRole)
        if value:
            editor.setCurrentText(str(value))
    
    def setModelData(self, editor, model, index):
        value = editor.currentText()
        model.setData(index, value, Qt.ItemDataRole.EditRole)
        
        if self.on_commit:
            self.on_commit(index.row(), index.column(), value)
    
    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


class InlineCheckDelegate(QItemDelegate):
    """Делегат для CheckBox (isCrit, isFocus)"""
    
    def createEditor(self, parent, option, index):
        editor = QCheckBox(parent)
        editor.setStyleSheet("background: white;")
        return editor
    
    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.ItemDataRole.EditRole)
        editor.setChecked(bool(value) if value else False)
    
    def setModelData(self, editor, model, index):
        value = 1 if editor.isChecked() else 0
        model.setData(index, value, Qt.ItemDataRole.EditRole)
        
        if self.on_commit:
            self.on_commit(index.row(), index.column(), value)
    
    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


class InlineUserDelegate(QItemDelegate):
    """Делегат для Responsible QA/Dev (ComboBox с пользователями)"""
    
    def __init__(self, parent=None, users=None, on_commit=None):
        super().__init__(parent)
        self.users = users or []  # Список имён пользователей
        self.on_commit = on_commit
    
    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        editor.setEditable(True)  # Можно ввести вручную
        editor.addItems([''] + self.users)
        editor.setStyleSheet("background: white; border: 2px solid #0078d7;")
        return editor
    
    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.ItemDataRole.EditRole)
        if value:
            editor.setCurrentText(str(value))
    
    def setModelData(self, editor, model, index):
        value = editor.currentText()
        model.setData(index, value, Qt.ItemDataRole.EditRole)
        
        if self.on_commit:
            self.on_commit(index.row(), index.column(), value)
    
    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)
    
    def update_users(self, users):
        """Обновление списка пользователей"""
        self.users = users
