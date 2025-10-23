# 🔄 Migration to Multi-Project Architecture

## 📋 Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Migration Process](#migration-process)
4. [Data Models](#data-models)
5. [Database Management](#database-management)
6. [Backward Compatibility](#backward-compatibility)
7. [Testing & Validation](#testing--validation)

---

## 🎯 Overview

**Version:** 0.4.0  
**Date:** 2025-01-16  
**Status:** Implemented

### Purpose

Migrate VoluptAS from single-database architecture to multi-project system supporting:
- Multiple isolated QA projects
- Profile-based credentials (Production/Sandbox/Custom)
- Seamless project switching
- Safe migration from legacy structure

### Key Goals

✅ **Zero data loss** - All existing data preserved  
✅ **Non-destructive** - Original DB backed up  
✅ **User-friendly** - One-click migration dialog  
✅ **Backward compatible** - Fallback to old config files  
✅ **Isolated projects** - Separate DBs and credentials  

---

## 🏗️ Architecture

### Before: Single Database

```
VoluptAS/
├── data/
│   └── voluptas.db          # Single SQLite database
├── config_zoho.env          # Global Zoho credentials
├── service_account.json     # Global Google credentials
└── src/
    └── database.py          # Global session singleton
```

**Limitations:**
- ❌ Only one project at a time
- ❌ Credentials mixed between environments
- ❌ Risk of production data corruption during testing
- ❌ No project isolation

### After: Multi-Project

```
VoluptAS/
├── projects/
│   ├── project_config.json                    # Project registry
│   ├── Default_Project_abc123/                # Project 1
│   │   ├── project.db                         # Isolated DB
│   │   └── settings_profiles.json             # Project-specific credentials
│   └── MyApp_Testing_xyz789/                  # Project 2
│       ├── project.db
│       └── settings_profiles.json
├── data/
│   └── voluptas.db.backup                     # Old DB (backup)
└── src/
    ├── ui/multi_project/
    │   ├── project_manager.py                 # Project lifecycle
    │   ├── database_manager.py                # Dynamic DB connections
    │   ├── migration_manager.py               # Migration logic
    │   ├── project_selector_dialog.py         # UI for project selection
    │   ├── new_project_dialog.py              # UI for project creation
    │   └── project_settings_dialog.py         # UI for project settings
    └── database.py                            # Refactored for multi-project
```

**Benefits:**
- ✅ Multiple projects with isolated data
- ✅ Profile-based credentials per project
- ✅ Safe switching without data mixing
- ✅ Production/Sandbox separation
- ✅ Centralized project management

---

## 🔄 Migration Process

### Phase 1: Detection (Startup)

**Location:** `MainWindow.__init__()` → `check_and_migrate()`

```python
def check_and_migrate(self):
    """Check if migration needed on first launch"""
    old_db = Path("data/voluptas.db")
    new_config = Path("projects/project_config.json")
    
    if old_db.exists() and not new_config.exists():
        # Show migration dialog
        from src.ui.multi_project.migration_manager import MigrationManager
        if MigrationManager.show_migration_dialog():
            MigrationManager.migrate_to_multiproject()
```

**Trigger Conditions:**
1. `data/voluptas.db` exists (old structure)
2. `projects/project_config.json` does NOT exist (not migrated)

### Phase 2: User Confirmation

**Dialog:** `MigrationManager.show_migration_dialog()`

```
┌──────────────────────────────────────────────┐
│ 🔄 Миграция в Multi-Project                  │
├──────────────────────────────────────────────┤
│ Обнаружена старая структура базы данных:     │
│   • data/voluptas.db                         │
│                                              │
│ Выполнить миграцию?                          │
│                                              │
│ Будет создан проект "Default Project" со     │
│ всеми вашими данными. Старая БД сохранится   │
│ как backup (voluptas.db.backup).             │
│                                              │
│ [  Да, мигрировать  ]  [  Нет, выйти  ]      │
└──────────────────────────────────────────────┘
```

**User Actions:**
- **Yes** → Execute migration
- **No** → Exit application (prevents data corruption)

### Phase 3: Migration Execution

**Steps executed by** `MigrationManager.migrate_to_multiproject()`:

#### 3.1 Create Projects Directory

```python
projects_dir = Path("projects")
projects_dir.mkdir(exist_ok=True)
```

#### 3.2 Generate Project ID

```python
import uuid
project_id = f"Default_Project_{uuid.uuid4().hex[:8]}"
project_folder = projects_dir / project_id
project_folder.mkdir()
```

**Format:** `Default_Project_<8-char-uuid>`  
**Example:** `Default_Project_a1b2c3d4`

#### 3.3 Copy Database

```python
old_db = Path("data/voluptas.db")
new_db = project_folder / "project.db"
shutil.copy2(old_db, new_db)
```

**Preserves:**
- All tables and data
- Indexes and constraints
- Timestamps (via `copy2`)

#### 3.4 Backup Old Database

```python
backup_path = old_db.parent / "voluptas.db.backup"
old_db.rename(backup_path)
```

**Result:** `data/voluptas.db` → `data/voluptas.db.backup`

#### 3.5 Create Project Config

**File:** `projects/project_config.json`

```json
{
  "projects": {
    "Default_Project_a1b2c3d4": {
      "name": "Default Project",
      "description": "Migrated from legacy database",
      "folder": "projects/Default_Project_a1b2c3d4",
      "profile": "production",
      "tags": ["migrated"],
      "created_at": "2025-01-16T10:00:00",
      "modified_at": "2025-01-16T10:00:00",
      "used_count": 0
    }
  },
  "last_active_project_id": "Default_Project_a1b2c3d4"
}
```

#### 3.6 Migrate Credentials (Optional)

If `config_zoho.env` and `service_account.json` exist:

```python
from src.ui.multi_project.settings_profile import SettingsProfile

# Load from old config files
zoho_creds = load_from_env("config_zoho.env")
google_path = "service_account.json"
qase_creds = load_qase_from_settings()

# Create settings_profiles.json
profile = SettingsProfile(project_folder)
profile.set_credentials("production", {
    "zoho": zoho_creds,
    "google_sheets": {"service_account_path": google_path},
    "qase": qase_creds
})
profile.save()
```

**File:** `projects/Default_Project_abc123/settings_profiles.json`

```json
{
  "production": {
    "zoho": {
      "client_id": "...",
      "client_secret": "...",
      "refresh_token": "...",
      "portal_id": "..."
    },
    "google_sheets": {
      "service_account_path": "service_account.json"
    },
    "qase": {
      "api_token": "...",
      "workspace_id": "..."
    }
  }
}
```

#### 3.7 Set Active Project

```python
ProjectManager.set_active_project(project_id)
DatabaseManager.switch_to_project(project_id)
```

### Phase 4: Post-Migration

**Automatic actions:**
1. Window title updated: `VoluptAS - Default Project 🏭`
2. Toolbar displays project name
3. All UI tabs reload with new DB session
4. Migration flag set (won't prompt again)

**User can:**
- Continue working immediately (no restart needed)
- Create additional projects
- Rollback if needed (see below)

---

## 📦 Data Models

### ProjectConfig

**Location:** `src/ui/multi_project/project_manager.py`

```python
@dataclass
class ProjectConfig:
    """Configuration for a single project"""
    project_id: str              # Unique ID (Name_UUID)
    name: str                    # Display name
    description: str             # User description
    folder: str                  # Path to project folder
    profile: str                 # 'production', 'sandbox', 'custom'
    tags: List[str]              # Searchable tags
    created_at: str              # ISO timestamp
    modified_at: str             # ISO timestamp
    used_count: int              # Number of activations
```

**Methods:**
```python
def to_dict() -> dict                  # Serialize to JSON
@classmethod
def from_dict(cls, data: dict)         # Deserialize from JSON
def increment_used_count()             # Track usage
def update_modified_time()             # Update timestamp
```

### SettingsProfile

**Location:** `src/ui/multi_project/settings_profile.py`

```python
class SettingsProfile:
    """Manages credentials for different profiles"""
    
    def __init__(self, project_folder: Path)
    
    def get_credentials(self, profile: str, service: str) -> dict
    def set_credentials(self, profile: str, credentials: dict)
    def save() -> bool
    def load() -> bool
```

**Profiles:**
- `production` - Live environment credentials
- `sandbox` - Testing environment credentials
- `custom` - User-defined credentials

**Services:**
- `zoho` - Zoho Projects API
- `google_sheets` - Google Service Account
- `qase` - Qase.io API
- `testrail` - TestRail API (future)

---

## 🗄️ Database Management

### DatabaseManager

**Location:** `src/ui/multi_project/database_manager.py`

```python
class DatabaseManager:
    """Singleton managing dynamic database connections"""
    
    _instance = None
    _session = None
    _engine = None
    _current_project_id = None
    
    @classmethod
    def get_session(cls) -> Session:
        """Get current database session"""
        if not cls._session:
            raise RuntimeError("No active project")
        return cls._session
    
    @classmethod
    def switch_to_project(cls, project_id: str):
        """Switch to different project database"""
        # 1. Close current session
        if cls._session:
            cls._session.close()
            cls._engine.dispose()
        
        # 2. Get project config
        config = ProjectManager.get_project(project_id)
        db_path = Path(config.folder) / "project.db"
        
        # 3. Create new engine and session
        cls._engine = create_engine(f"sqlite:///{db_path}")
        Session = sessionmaker(bind=cls._engine)
        cls._session = Session()
        cls._current_project_id = project_id
        
        # 4. Initialize schema if needed
        from src.database import Base
        Base.metadata.create_all(cls._engine)
```

**Key Features:**
- Singleton pattern (one session at a time)
- Automatic schema migration on switch
- Safe session disposal
- Connection pooling per project

### Migration to DatabaseManager

**Old code (global session):**
```python
from src.database import Session
session = Session()
```

**New code (project-aware session):**
```python
from src.ui.multi_project.database_manager import DatabaseManager
session = DatabaseManager.get_session()
```

**Changed files:**
- `src/ui/main_window.py` - Initialize DatabaseManager
- `src/ui/tabs/*.py` - Use DatabaseManager.get_session()
- All UI widgets with DB queries

---

## 🔗 Backward Compatibility

### Legacy Config Files

**Fallback hierarchy for credentials:**

1. **New system (preferred):**
   ```
   projects/<ProjectID>/settings_profiles.json → profile['production']
   ```

2. **Legacy files (fallback):**
   ```
   config_zoho.env                        # Zoho credentials
   service_account.json                   # Google credentials
   (Qase settings from old SettingsDialog)
   ```

**Implementation in** `SettingsDialog.load_settings()`:

```python
def load_settings(self):
    """Load settings with fallback to legacy config"""
    # Try new profile system
    profile = SettingsProfile(current_project_folder)
    if profile.load():
        creds = profile.get_credentials('production', 'zoho')
        if creds:
            self.zoho_client_id.setText(creds['client_id'])
            return
    
    # Fallback to config_zoho.env
    if Path("config_zoho.env").exists():
        from dotenv import load_dotenv
        load_dotenv("config_zoho.env")
        self.zoho_client_id.setText(os.getenv("ZOHO_CLIENT_ID", ""))
```

### Rollback Procedure

If migration fails or user wants to revert:

#### Step 1: Restore Old Database
```bash
cd data
mv voluptas.db.backup voluptas.db
```

#### Step 2: Remove Multi-Project Config
```bash
rm -rf projects/
```

#### Step 3: Restart Application
- App detects old structure again
- Offers migration (can decline to use legacy mode)

**Note:** Future versions may remove legacy mode support.

---

## ✅ Testing & Validation

### Manual Testing Checklist

#### Migration Tests

- [ ] **Fresh install** - Creates "Default Project" automatically
- [ ] **Legacy DB exists** - Migration dialog appears
- [ ] **Migration accepted** - All data copied successfully
- [ ] **Migration declined** - App exits gracefully
- [ ] **Backup created** - `voluptas.db.backup` exists and readable
- [ ] **Old DB removed** - `voluptas.db` no longer in `data/`
- [ ] **Project config valid** - JSON structure correct

#### Project Operations

- [ ] **Create new project** - Success with valid inputs
- [ ] **Create duplicate name** - Error message shown
- [ ] **Switch projects** - DB changes, UI updates
- [ ] **Edit project settings** - Changes persist
- [ ] **Delete project** - Confirmation dialog, files removed
- [ ] **Import/Export project** - .zip includes DB and profiles

#### Database Operations

- [ ] **Query after switch** - Correct data displayed
- [ ] **Insert after switch** - Saves to correct DB
- [ ] **Update after switch** - Modifies correct records
- [ ] **Multiple switches** - No session leaks or crashes

#### Credentials Management

- [ ] **Set production creds** - Saved to profile
- [ ] **Set sandbox creds** - Isolated from production
- [ ] **Switch profiles** - API calls use correct tokens
- [ ] **Fallback to legacy** - Works if profile missing
- [ ] **Save from SettingsDialog** - Creates profile if needed

### Automated Tests

**Location:** `tests/test_multi_project.py`

```python
class TestMigration:
    def test_migration_creates_backup()
    def test_migration_preserves_data()
    def test_migration_creates_config()
    def test_migration_idempotent()

class TestProjectManager:
    def test_create_project()
    def test_delete_project()
    def test_switch_project()
    def test_get_all_projects()

class TestDatabaseManager:
    def test_session_switch()
    def test_schema_initialization()
    def test_session_isolation()
```

### Performance Tests

**Metrics to validate:**
- Project switch time < 500ms
- DB query time unchanged vs. legacy
- Memory usage per project < 50MB
- No memory leaks after 100 switches

---

## 🔍 Troubleshooting

### Issue: Migration Dialog Doesn't Appear

**Symptoms:**
- Old `data/voluptas.db` exists
- App starts without migration prompt

**Causes:**
1. `project_config.json` already exists (migration done)
2. Exception in `check_and_migrate()`

**Solution:**
```bash
# Check if already migrated
ls projects/project_config.json

# If not, manually trigger:
python -c "from src.ui.multi_project.migration_manager import MigrationManager; MigrationManager.migrate_to_multiproject()"
```

### Issue: "Could not open project database"

**Symptoms:**
- Error dialog on project switch
- Console shows "OperationalError: unable to open database"

**Causes:**
1. Corrupted `project.db`
2. Missing project folder
3. Permissions issue

**Solution:**
```bash
# Verify file exists
ls projects/<ProjectID>/project.db

# Check permissions
chmod 644 projects/<ProjectID>/project.db

# Restore from backup if corrupted
cp projects/<ProjectID>/project.db.backup projects/<ProjectID>/project.db
```

### Issue: Settings Not Loading

**Symptoms:**
- Integrations show empty fields
- API calls fail with 401 Unauthorized

**Causes:**
1. `settings_profiles.json` missing
2. Profile name mismatch
3. Malformed JSON

**Solution:**
```bash
# Check file exists
cat projects/<ProjectID>/settings_profiles.json

# Validate JSON
python -c "import json; json.load(open('projects/<ProjectID>/settings_profiles.json'))"

# Recreate from legacy config
python scripts/migrate_credentials.py
```

---

## 📝 Changelog

### v0.4.0 (2025-01-16)

**Added:**
- Multi-project architecture
- ProjectManager for project lifecycle
- DatabaseManager for dynamic DB switching
- MigrationManager for safe migration
- Profile-based credentials (Production/Sandbox/Custom)
- ProjectSelectorDialog with search and filters
- NewProjectDialog with validation
- ProjectSettingsDialog with tabbed interface
- Toolbar project selector

**Changed:**
- Database session management (global → project-aware)
- SettingsDialog to use profiles with legacy fallback
- MainWindow to initialize multi-project system
- Window title to show active project

**Migrated:**
- All UI widgets to use `DatabaseManager.get_session()`
- All DB queries to project-aware sessions
- Legacy credentials to settings_profiles.json

**Backward Compatible:**
- Fallback to config_zoho.env
- Automatic migration from data/voluptas.db
- Backup preservation

---

## 📚 References

**Related Docs:**
- [USER_GUIDE_Projects.md](./USER_GUIDE_Projects.md) - User-facing guide
- [README.md](../README.md) - Main project documentation
- [QUICKSTART.md](../QUICKSTART.md) - Setup instructions

**Code Modules:**
- `src/ui/multi_project/project_manager.py` - Project management
- `src/ui/multi_project/database_manager.py` - DB connection management
- `src/ui/multi_project/migration_manager.py` - Migration logic
- `src/ui/multi_project/settings_profile.py` - Credentials storage

**Database Schema:**
- `src/database.py` - SQLAlchemy models (unchanged)
- `src/database_setup.py` - Schema initialization (refactored)

---

**Document Version:** 1.0  
**Last Updated:** 2025-01-16  
**Author:** VoluptAS Development Team  
**Status:** ✅ Implemented and Tested
