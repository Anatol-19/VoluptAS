# Credentials

Эта папка содержит конфиденциальные файлы для интеграций.

⚠️ **ВАЖНО:** НЕ КОММИТИТЬ эти файлы в Git! (Уже в .gitignore)

---

## 📂 Файлы

### 1. `zoho.env` - Zoho Projects API

**✨ Рекомендуется:** Используйте 🧙 **OAuth Wizard** в UI!

**Автоматическая настройка:**
1. Откройте приложение
2. Файл → Настройки → Zoho
3. Нажмите "🧙 Запустить OAuth Wizard"
4. Следуйте инструкциям (5 шагов)
5. Токены автоматически сохранятся в этот файл

**Ручная настройка:**
```env
ZOHO_CLIENT_ID=1000.XXXXXXXXXXXXXXXXXXXX
ZOHO_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ZOHO_AUTHORIZATION_CODE=  # Не обязательно
ZOHO_REGION=com
ZOHO_ACCESS_TOKEN=  # Автообновляется
ZOHO_REFRESH_TOKEN=1000.xxxxxxxxxxxxxxxxxxxxxxxxxxxx
ZOHO_PORTAL_NAME=vrbgroup
ZOHO_PROJECT_ID=1209515000001238053
```

---

### 2. `google_service_account.json` - Google API

**Как получить:**
1. [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте Service Account
3. Включите API: Sheets, Drive
4. Скачайте JSON ключ
5. Сохраните как `google_service_account.json`

**Или через UI:**
- Файл → Настройки → Google
- Вставьте JSON в текстовое поле

---

### 3. `qase.env` - Qase.io API

```env
QASE_API_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
QASE_PROJECT_CODE=ITS
QASE_BASE_URL=https://api.qase.io/v1
```

**Как получить:**
1. [Qase.io](https://app.qase.io/)
2. Settings → API Tokens
3. Create New Token
4. Скопируйте и вставьте в файл

**Или через UI:**
- Файл → Настройки → Qase

---

## 🔒 Безопасность

- ✅ Все файлы в `.gitignore`
- ❌ НИКОГДА не коммитьте эти файлы
- 🔐 Токены автоматически обновляются
- 💾 Сохраняйте backup в безопасном месте

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
