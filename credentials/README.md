# Credentials - СЕКРЕТЫ

⚠️ **НЕ КОММИТИТЬ ЭТУ ПАПКУ В GIT!**

Эта папка содержит все credentials для внешних сервисов.

---

## 📁 Структура

```
credentials/
├── google_service_account.json  # Google Sheets API credentials
├── zoho.env                     # Zoho Projects API credentials
└── README.md                    # Этот файл (безопасно коммитить)
```

---

## 🔐 Google Sheets

**Файл**: `google_service_account.json`

### Как получить:
1. Перейти в [Google Cloud Console](https://console.cloud.google.com/)
2. Создать/выбрать проект
3. Включить Google Sheets API
4. Создать Service Account
5. Скачать JSON ключ
6. Сохранить как `google_service_account.json`

### Использование:
```python
from src.integrations.google import GoogleSheetsClient

client = GoogleSheetsClient(
    credentials_path="credentials/google_service_account.json",
    spreadsheet_id="your_spreadsheet_id",
    worksheet_name="Sheet1"
)
```

---

## 🔐 Zoho Projects

**Файл**: `zoho.env`

### Структура:
```env
ZOHO_CLIENT_ID=...
ZOHO_CLIENT_SECRET=...
ZOHO_REFRESH_TOKEN=...
ZOHO_ACCESS_TOKEN=...  # Автообновляется
ZOHO_PROJECT_ID=...
ZOHO_PORTAL_NAME=...
ZOHO_REGION=com
ZOHO_AUTHORIZATION_CODE=...
ZOHO_REDIRECT_URI=...
```

### Как получить:
1. Зарегистрировать приложение в [Zoho API Console](https://api-console.zoho.com/)
2. Получить Client ID и Client Secret
3. Авторизовать приложение (получить Authorization Code)
4. Обменять на Refresh Token

### Использование:
```python
from src.integrations.zoho import ZohoAPI

api = ZohoAPI()  # Автоматически читает credentials/zoho.env
```

⚠️ **Access Token обновляется автоматически!**

---

## ✅ Безопасность

### Что в .gitignore:
```gitignore
credentials/*.json
credentials/*.env
!credentials/README.md
```

### Что коммитить:
- ✅ `README.md` (этот файл)
- ❌ `.json` файлы
- ❌ `.env` файлы

---

## 📝 Backup

Рекомендуется хранить backup credentials в безопасном месте:
- Password manager (1Password, LastPass)
- Зашифрованное хранилище
- Корпоративный vault

**НЕ ХРАНИТЕ В:**
- Git репозиториях
- Открытых облачных хранилищах
- Email переписках
- Мессенджерах

---

**Последнее обновление**: 2025-10-13
