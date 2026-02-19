"""
Модель конфигурации проекта

Поддерживает:
- Множественные проекты с отдельными БД
- Профили настроек (production, sandbox)
- Переключение между проектами
"""

from dataclasses import dataclass
from typing import Optional, Dict, List
from pathlib import Path
import json
from datetime import datetime


@dataclass
class ProjectConfig:
    """Конфигурация одного проекта"""

    # Основные параметры
    id: str  # Уникальный ID проекта (slug)
    name: str  # Название проекта
    description: str  # Описание

    # Пути
    database_path: Path  # Путь к БД проекта
    bdd_features_dir: Path  # Директория BDD features
    reports_dir: Path  # Директория отчётов

    # Профиль настроек
    settings_profile: str  # production | sandbox | custom

    # Метаданные
    created_at: str
    last_used: Optional[str] = None
    is_active: bool = True

    # Дополнительные настройки
    tags: List[str] = None
    custom_fields: Dict = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.custom_fields is None:
            self.custom_fields = {}

    def to_dict(self) -> Dict:
        """Сериализация в словарь"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "database_path": str(self.database_path),
            "bdd_features_dir": str(self.bdd_features_dir),
            "reports_dir": str(self.reports_dir),
            "settings_profile": self.settings_profile,
            "created_at": self.created_at,
            "last_used": self.last_used,
            "is_active": self.is_active,
            "tags": self.tags,
            "custom_fields": self.custom_fields,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "ProjectConfig":
        """Десериализация из словаря"""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            database_path=Path(data["database_path"]),
            bdd_features_dir=Path(data["bdd_features_dir"]),
            reports_dir=Path(data["reports_dir"]),
            settings_profile=data["settings_profile"],
            created_at=data["created_at"],
            last_used=data.get("last_used"),
            is_active=data.get("is_active", True),
            tags=data.get("tags", []),
            custom_fields=data.get("custom_fields", {}),
        )


@dataclass
class SettingsProfile:
    """Профиль настроек интеграций"""

    id: str  # production | sandbox | custom
    name: str  # Название профиля
    description: str  # Описание

    # Пути к credentials
    zoho_env_path: Optional[Path] = None
    google_json_path: Optional[Path] = None
    qase_env_path: Optional[Path] = None

    # Метаданные
    created_at: str = None
    is_default: bool = False

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "zoho_env_path": str(self.zoho_env_path) if self.zoho_env_path else None,
            "google_json_path": (
                str(self.google_json_path) if self.google_json_path else None
            ),
            "qase_env_path": str(self.qase_env_path) if self.qase_env_path else None,
            "created_at": self.created_at,
            "is_default": self.is_default,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "SettingsProfile":
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            zoho_env_path=(
                Path(data["zoho_env_path"]) if data.get("zoho_env_path") else None
            ),
            google_json_path=(
                Path(data["google_json_path"]) if data.get("google_json_path") else None
            ),
            qase_env_path=(
                Path(data["qase_env_path"]) if data.get("qase_env_path") else None
            ),
            created_at=data.get("created_at"),
            is_default=data.get("is_default", False),
        )


class ProjectManager:
    """Менеджер проектов - управление несколькими проектами"""

    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.config_file = config_dir / "projects.json"
        self.profiles_file = config_dir / "profiles.json"
        self.current_project_file = config_dir / "current_project.txt"

        self.config_dir.mkdir(exist_ok=True, parents=True)

        self.projects: Dict[str, ProjectConfig] = {}
        self.profiles: Dict[str, SettingsProfile] = {}
        self.current_project_id: Optional[str] = None

        self.load()

    def load(self):
        """Загрузка конфигурации"""
        # Загрузка проектов
        if self.config_file.exists():
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.projects = {
                    proj_id: ProjectConfig.from_dict(proj_data)
                    for proj_id, proj_data in data.items()
                }

        # Загрузка профилей
        if self.profiles_file.exists():
            with open(self.profiles_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.profiles = {
                    prof_id: SettingsProfile.from_dict(prof_data)
                    for prof_id, prof_data in data.items()
                }

        # Загрузка текущего проекта
        if self.current_project_file.exists():
            self.current_project_id = self.current_project_file.read_text(
                encoding="utf-8"
            ).strip()

        # Создание дефолтных профилей если нет
        if not self.profiles:
            self._create_default_profiles()

    def save(self):
        """Сохранение конфигурации"""
        # Сохранение проектов
        with open(self.config_file, "w", encoding="utf-8") as f:
            data = {proj_id: proj.to_dict() for proj_id, proj in self.projects.items()}
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Сохранение профилей
        with open(self.profiles_file, "w", encoding="utf-8") as f:
            data = {prof_id: prof.to_dict() for prof_id, prof in self.profiles.items()}
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Сохранение текущего проекта
        if self.current_project_id:
            self.current_project_file.write_text(
                self.current_project_id, encoding="utf-8"
            )

    def create_project(
        self,
        project_id: str,
        name: str,
        description: str,
        settings_profile: str = "production",
    ) -> ProjectConfig:
        """Создание нового проекта"""
        if project_id in self.projects:
            raise ValueError(f'Проект с ID "{project_id}" уже существует')

        # Создание директорий проекта
        project_dir = self.config_dir.parent / "projects" / project_id
        project_dir.mkdir(exist_ok=True, parents=True)

        # --- Изменено: имя БД зависит от проекта ---
        if project_id == "default":
            db_path = project_dir / "voluptas.db"
        else:
            db_path = project_dir / f"{project_id}.db"
        bdd_dir = project_dir / "bdd_features"
        reports_dir = project_dir / "reports"

        bdd_dir.mkdir(exist_ok=True)
        reports_dir.mkdir(exist_ok=True)

        project = ProjectConfig(
            id=project_id,
            name=name,
            description=description,
            database_path=db_path,
            bdd_features_dir=bdd_dir,
            reports_dir=reports_dir,
            settings_profile=settings_profile,
            created_at=datetime.now().isoformat(),
            is_active=True,
        )

        self.projects[project_id] = project
        self.save()

        return project

    def get_current_project(self) -> Optional[ProjectConfig]:
        """Получить текущий активный проект"""
        if self.current_project_id and self.current_project_id in self.projects:
            return self.projects[self.current_project_id]
        return None

    def switch_project(self, project_id: str):
        """Переключение на другой проект"""
        if project_id not in self.projects:
            raise ValueError(f'Проект "{project_id}" не найден')

        self.current_project_id = project_id

        # Обновляем last_used
        self.projects[project_id].last_used = datetime.now().isoformat()

        self.save()

    def list_projects(self) -> List[ProjectConfig]:
        """Список всех проектов"""
        return list(self.projects.values())

    def get_profile(self, profile_id: str) -> Optional[SettingsProfile]:
        """Получить профиль настроек"""
        return self.profiles.get(profile_id)

    def _create_default_profiles(self):
        """Создание дефолтных профилей"""
        cred_dir = self.config_dir.parent / "credentials"

        # Production профиль
        self.profiles["production"] = SettingsProfile(
            id="production",
            name="Production",
            description="Основной профиль для рабочих проектов",
            zoho_env_path=cred_dir / "zoho.env",
            google_json_path=cred_dir / "google_credentials.json",
            qase_env_path=cred_dir / "qase.env",
            created_at=datetime.now().isoformat(),
            is_default=True,
        )

        # Sandbox профиль
        self.profiles["sandbox"] = SettingsProfile(
            id="sandbox",
            name="Sandbox",
            description="Тестовый профиль для экспериментов",
            zoho_env_path=cred_dir / "sandbox" / "zoho.env",
            google_json_path=cred_dir / "sandbox" / "google_credentials.json",
            qase_env_path=cred_dir / "sandbox" / "qase.env",
            created_at=datetime.now().isoformat(),
            is_default=False,
        )

        self.save()
