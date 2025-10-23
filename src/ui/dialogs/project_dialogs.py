"""
Project Management Dialogs

- ProjectSelectorDialog: Выбор проекта
- NewProjectDialog: Создание нового проекта
- ProjectSettingsDialog: Настройки проекта
"""

from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from pathlib import Path
from typing import Optional
import re
import logging

logger = logging.getLogger(__name__)


class ProjectSelectorDialog(QDialog):
    """Диалог выбора проекта"""
    
    project_selected = pyqtSignal(str)  # project_id
    
    def __init__(self, project_manager, parent=None):
        super().__init__(parent)
        self.project_manager = project_manager
        self.selected_project_id = None
        
        self.setWindowTitle('Выбор проекта')
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        self.init_ui()
        self.load_projects()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Заголовок
        title = QLabel('Выберите проект для работы')
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Поиск
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel('🔍'))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('Поиск по названию или описанию...')
        self.search_input.textChanged.connect(self.filter_projects)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # Список проектов
        self.projects_list = QListWidget()
        self.projects_list.setAlternatingRowColors(True)
        self.projects_list.itemDoubleClicked.connect(self.on_project_double_click)
        self.projects_list.itemSelectionChanged.connect(self.on_selection_changed)
        layout.addWidget(self.projects_list)
        
        # Информация о выбранном проекте
        info_group = QGroupBox('Информация о проекте')
        info_layout = QFormLayout(info_group)
        
        self.info_name = QLabel('-')
        self.info_description = QLabel('-')
        self.info_description.setWordWrap(True)
        self.info_profile = QLabel('-')
        self.info_last_used = QLabel('-')
        self.info_db_size = QLabel('-')
        
        info_layout.addRow('Название:', self.info_name)
        info_layout.addRow('Описание:', self.info_description)
        info_layout.addRow('Профиль:', self.info_profile)
        info_layout.addRow('Последнее использование:', self.info_last_used)
        info_layout.addRow('Размер БД:', self.info_db_size)
        
        layout.addWidget(info_group)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        new_project_btn = QPushButton('➕ Новый проект')
        new_project_btn.clicked.connect(self.create_new_project)
        buttons_layout.addWidget(new_project_btn)
        
        self.delete_btn = QPushButton('🗑️ Удалить проект')
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self.delete_project)
        self.delete_btn.setStyleSheet('color: #d32f2f;')
        buttons_layout.addWidget(self.delete_btn)
        
        buttons_layout.addStretch()
        
        self.select_btn = QPushButton('Выбрать')
        self.select_btn.setEnabled(False)
        self.select_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(self.select_btn)
        
        cancel_btn = QPushButton('Отмена')
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
    
    def load_projects(self):
        """Загрузка списка проектов"""
        self.projects_list.clear()
        
        projects = self.project_manager.list_projects()
        
        # Сортируем: сначала активные, потом по last_used
        active_projects = [p for p in projects if p.is_active]
        active_projects.sort(key=lambda p: p.last_used or '0', reverse=True)
        
        for project in active_projects:
            # Форматирование элемента
            profile_emoji = '🏭' if project.settings_profile == 'production' else '🧪'
            
            item_text = f"{profile_emoji} {project.name}"
            if project.last_used:
                from datetime import datetime
                try:
                    last_used = datetime.fromisoformat(project.last_used)
                    time_ago = self.get_time_ago(last_used)
                    item_text += f" (использовался {time_ago})"
                except:
                    pass
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, project.id)
            self.projects_list.addItem(item)
        
        # Автовыбор текущего проекта
        current_project = self.project_manager.get_current_project()
        if current_project:
            for i in range(self.projects_list.count()):
                item = self.projects_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == current_project.id:
                    self.projects_list.setCurrentItem(item)
                    break
    
    def filter_projects(self):
        """Фильтрация проектов по поисковому запросу"""
        search_text = self.search_input.text().lower()
        
        for i in range(self.projects_list.count()):
            item = self.projects_list.item(i)
            project_id = item.data(Qt.ItemDataRole.UserRole)
            project = self.project_manager.projects.get(project_id)
            
            if project:
                match = (
                    search_text in project.name.lower() or
                    search_text in (project.description or '').lower() or
                    search_text in project_id.lower()
                )
                item.setHidden(not match)
    
    def on_selection_changed(self):
        """Обработка изменения выбора"""
        selected_items = self.projects_list.selectedItems()
        
        if not selected_items:
            self.select_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            self.clear_info()
            return
        
        self.select_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)
        
        item = selected_items[0]
        project_id = item.data(Qt.ItemDataRole.UserRole)
        project = self.project_manager.projects.get(project_id)
        
        if project:
            self.selected_project_id = project_id
            self.show_project_info(project)
    
    def show_project_info(self, project):
        """Показать информацию о проекте"""
        self.info_name.setText(project.name)
        self.info_description.setText(project.description or 'Нет описания')
        
        profile_name = {
            'production': '🏭 Production',
            'sandbox': '🧪 Sandbox',
            'custom': '⚙️ Custom'
        }.get(project.settings_profile, project.settings_profile)
        self.info_profile.setText(profile_name)
        
        if project.last_used:
            from datetime import datetime
            try:
                last_used = datetime.fromisoformat(project.last_used)
                self.info_last_used.setText(last_used.strftime('%Y-%m-%d %H:%M:%S'))
            except:
                self.info_last_used.setText('Неизвестно')
        else:
            self.info_last_used.setText('Никогда')
        
        # Размер БД
        if project.database_path.exists():
            size_bytes = project.database_path.stat().st_size
            size_mb = size_bytes / (1024 * 1024)
            self.info_db_size.setText(f'{size_mb:.2f} MB')
        else:
            self.info_db_size.setText('БД не найдена')
    
    def clear_info(self):
        """Очистить информацию"""
        self.info_name.setText('-')
        self.info_description.setText('-')
        self.info_profile.setText('-')
        self.info_last_used.setText('-')
        self.info_db_size.setText('-')
    
    def on_project_double_click(self, item):
        """Двойной клик - выбор проекта"""
        self.accept()
    
    def delete_project(self):
        """Удалить проект"""
        if not self.selected_project_id:
            return
        
        project = self.project_manager.projects.get(self.selected_project_id)
        if not project:
            return
        
        reply = QMessageBox.question(
            self, 'Подтвердите удаление',
            f'Вы уверены, что хотите удалить проект "{project.name}"?\n\n'
            '⚠️ Это действие нельзя отменить!\n'
            'Будут удалены: БД, отчёты, BDD фичи.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            import shutil
            del self.project_manager.projects[self.selected_project_id]
            self.project_manager.save()
            
            project_dir = project.database_path.parent
            if project_dir.exists():
                shutil.rmtree(project_dir)
            
            logger.info(f"✅ Проект {self.selected_project_id} удалён")
            QMessageBox.information(self, 'Успех', f'✅ Проект "{project.name}" удалён')
            
            self.selected_project_id = None
            self.load_projects()
            
        except Exception as e:
            logger.error(f"❌ Ошибка удаления: {e}", exc_info=True)
            QMessageBox.critical(self, 'Ошибка', f'Не удалось удалить:\n{e}')
    
    def create_new_project(self):
        """Создание нового проекта"""
        dialog = NewProjectDialog(self.project_manager, self)
        if dialog.exec():
            # Обновляем список
            self.load_projects()
            # Автовыбираем новый проект
            new_project_id = dialog.created_project_id
            for i in range(self.projects_list.count()):
                item = self.projects_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == new_project_id:
                    self.projects_list.setCurrentItem(item)
                    break
    
    @staticmethod
    def get_time_ago(dt) -> str:
        """Получить строку 'X назад'"""
        from datetime import datetime, timedelta
        now = datetime.now()
        delta = now - dt
        
        if delta < timedelta(minutes=1):
            return 'только что'
        elif delta < timedelta(hours=1):
            minutes = int(delta.total_seconds() / 60)
            return f'{minutes} мин назад'
        elif delta < timedelta(days=1):
            hours = int(delta.total_seconds() / 3600)
            return f'{hours} ч назад'
        elif delta < timedelta(days=7):
            days = delta.days
            return f'{days} дн назад'
        elif delta < timedelta(days=30):
            weeks = delta.days // 7
            return f'{weeks} нед назад'
        else:
            months = delta.days // 30
            return f'{months} мес назад'


class NewProjectDialog(QDialog):
    """Диалог создания нового проекта"""
    
    def __init__(self, project_manager, parent=None):
        super().__init__(parent)
        self.project_manager = project_manager
        self.created_project_id = None
        
        self.setWindowTitle('Создание нового проекта')
        self.setMinimumWidth(500)
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Форма
        form = QFormLayout()
        
        # Название
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText('Например: Project B')
        self.name_edit.textChanged.connect(self.on_name_changed)
        form.addRow('* Название:', self.name_edit)
        
        # ID (автогенерация)
        self.id_edit = QLineEdit()
        self.id_edit.setPlaceholderText('Автогенерируется из названия')
        id_hint = QLabel('<i>Можно редактировать. Разрешены: a-z, 0-9, _, -</i>')
        id_hint.setStyleSheet('color: gray; font-size: 9pt;')
        form.addRow('* ID проекта:', self.id_edit)
        form.addRow('', id_hint)
        
        # Описание
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText('Краткое описание проекта')
        form.addRow('Описание:', self.description_edit)
        
        # Профиль
        self.profile_combo = QComboBox()
        profiles = self.project_manager.profiles.values()
        for profile in profiles:
            emoji = '🏭' if profile.id == 'production' else '🧪'
            self.profile_combo.addItem(f'{emoji} {profile.name} - {profile.description}', profile.id)
        
        # По умолчанию production
        default_idx = self.profile_combo.findData('production')
        if default_idx >= 0:
            self.profile_combo.setCurrentIndex(default_idx)
        
        form.addRow('Профиль настроек:', self.profile_combo)
        
        # Теги
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText('work, active (через запятую)')
        form.addRow('Теги:', self.tags_edit)
        
        layout.addLayout(form)
        
        # Кнопки
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.create_project)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText('Создать')
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText('Отмена')
        layout.addWidget(buttons)
    
    def on_name_changed(self, text):
        """Автогенерация ID из названия"""
        if not text:
            self.id_edit.clear()
            return
        
        # Генерируем slug
        slug = text.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s_-]+', '_', slug)
        slug = slug.strip('_-')
        
        self.id_edit.setText(slug)
    
    def create_project(self):
        """Создание проекта"""
        # Валидация
        name = self.name_edit.text().strip()
        project_id = self.id_edit.text().strip()
        
        if not name:
            QMessageBox.warning(self, 'Ошибка', 'Укажите название проекта')
            return
        
        if not project_id:
            QMessageBox.warning(self, 'Ошибка', 'Укажите ID проекта')
            return
        
        # Проверка валидности ID
        if not re.match(r'^[a-z0-9_-]+$', project_id):
            QMessageBox.warning(
                self, 'Ошибка',
                'ID проекта может содержать только: a-z, 0-9, _, -'
            )
            return
        
        # Проверка уникальности
        if project_id in self.project_manager.projects:
            QMessageBox.warning(self, 'Ошибка', f'Проект с ID "{project_id}" уже существует')
            return
        
        description = self.description_edit.toPlainText().strip()
        profile_id = self.profile_combo.currentData()
        tags_text = self.tags_edit.text().strip()
        tags = [t.strip() for t in tags_text.split(',') if t.strip()] if tags_text else []
        
        project = None
        db_path = None
        
        try:
            # Создаём проект
            project = self.project_manager.create_project(
                project_id=project_id,
                name=name,
                description=description,
                settings_profile=profile_id
            )
            
            project.tags = tags
            self.project_manager.save()
            
            # Инициализируем БД
            from src.db.database_manager import get_database_manager
            db_manager = get_database_manager()
            db_path = project.database_path
            db_manager.connect_to_database(db_path)
            db_manager.init_database()
            
            # Создаём дефолтного пользователя
            from src.models.user import User
            session = db_manager.get_session()
            try:
                default_user = User(
                    name='Default User',
                    position='QA',
                    email='user@example.com',
                    is_active=1
                )
                session.add(default_user)
                session.commit()
            finally:
                session.close()
            
            self.created_project_id = project_id
            
            QMessageBox.information(
                self, 'Успех',
                f'✅ Проект "{name}" создан успешно!\n\nМожно начать работу.'
            )
            
            self.accept()
            
        except Exception as e:
            logger.error(f"Ошибка создания проекта: {e}", exc_info=True)
            
            # Откат изменений
            if project:
                logger.info(f"🔄 Откат создания проекта {project_id}...")
                try:
                    # Удаляем из projects.json
                    if project_id in self.project_manager.projects:
                        del self.project_manager.projects[project_id]
                        self.project_manager.save()
                    
                    # Удаляем папку проекта
                    if db_path:
                        import shutil
                        project_dir = db_path.parent
                        if project_dir.exists():
                            shutil.rmtree(project_dir)
                            logger.info(f"✅ Папка проекта удалена: {project_dir}")
                    
                    logger.info("✅ Откат завершён")
                except Exception as rollback_error:
                    logger.error(f"⚠️ Ошибка отката: {rollback_error}")
            
            QMessageBox.critical(self, 'Ошибка', f'Не удалось создать проект:\n{e}\n\nИзменения отменены.')


class ProjectSettingsDialog(QDialog):
    """Диалог настроек проекта"""
    
    def __init__(self, project_manager, project_id, parent=None):
        super().__init__(parent)
        self.project_manager = project_manager
        self.project = project_manager.projects.get(project_id)
        
        if not self.project:
            raise ValueError(f'Проект "{project_id}" не найден')
        
        self.setWindowTitle(f'Настройки проекта: {self.project.name}')
        self.setMinimumWidth(500)
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Форма
        form = QFormLayout()
        
        # Название
        self.name_edit = QLineEdit(self.project.name)
        form.addRow('Название:', self.name_edit)
        
        # ID (readonly)
        id_label = QLabel(self.project.id)
        id_label.setStyleSheet('color: gray;')
        form.addRow('ID:', id_label)
        
        # Описание
        self.description_edit = QTextEdit(self.project.description or '')
        self.description_edit.setMaximumHeight(80)
        form.addRow('Описание:', self.description_edit)
        
        # Профиль
        self.profile_combo = QComboBox()
        profiles = self.project_manager.profiles.values()
        for profile in profiles:
            emoji = '🏭' if profile.id == 'production' else '🧪'
            self.profile_combo.addItem(f'{emoji} {profile.name}', profile.id)
        
        current_idx = self.profile_combo.findData(self.project.settings_profile)
        if current_idx >= 0:
            self.profile_combo.setCurrentIndex(current_idx)
        
        form.addRow('Профиль:', self.profile_combo)
        
        # Теги
        self.tags_edit = QLineEdit(', '.join(self.project.tags))
        form.addRow('Теги:', self.tags_edit)
        
        # Активен
        self.active_check = QCheckBox()
        self.active_check.setChecked(self.project.is_active)
        form.addRow('Активен:', self.active_check)
        
        layout.addLayout(form)
        
        # Кнопки
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.save_settings)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText('💾 Сохранить')
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText('Отмена')
        layout.addWidget(buttons)
    
    def save_settings(self):
        """Сохранение настроек"""
        name = self.name_edit.text().strip()
        
        if not name:
            QMessageBox.warning(self, 'Ошибка', 'Укажите название проекта')
            return
        
        self.project.name = name
        self.project.description = self.description_edit.toPlainText().strip() or None
        self.project.settings_profile = self.profile_combo.currentData()
        
        tags_text = self.tags_edit.text().strip()
        self.project.tags = [t.strip() for t in tags_text.split(',') if t.strip()] if tags_text else []
        
        self.project.is_active = self.active_check.isChecked()
        
        self.project_manager.save()
        
        QMessageBox.information(self, 'Успех', '✅ Настройки сохранены')
        self.accept()
