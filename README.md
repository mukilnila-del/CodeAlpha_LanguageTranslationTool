# 🌐 PolyGlot - Professional Language Translation Tool

A modern, responsive, and production-ready **Language Translation Web Application** built with **Python Flask**, HTML5, CSS3, and modern JavaScript. Featuring a luxury blue-and-purple gradient aesthetic, real-time bidirectional neural translation, full **LibreTranslate** API integration with automatic fallback resilience, audio pronunciation, text swapping, and clipboard copying.

---

## ✨ Features

- **🎨 Modern Blue & Purple Gradient Design**: Luxury glassmorphic panels, ambient gradient glow backdrops, smooth micro-interactions, and responsive layout for mobile, tablet, and desktop screens.
- **🌍 Real Multilingual Translation**: Authentic, 100% genuine translations across major languages:
  - **English (`en`)**
  - **Tamil (`ta`) - தமிழ்**
  - **Hindi (`hi`) - हिन्दी**
  - **French (`fr`) - Français**
  - **German (`de`) - Deutsch**
  - **Spanish (`es`) - Español**
  - Plus **Chinese (`zh`)**, **Japanese (`ja`)**, **Russian (`ru`)**, **Arabic (`ar`)**, **Italian (`it`)**, and **Portuguese (`pt`)**.
- **🔍 Auto-Detect Source Language**: Detects incoming text language automatically with a visual badge.
- **⚡ Dual-Engine Translation Strategy**:
  - Full **LibreTranslate** API integration with configurable endpoint and API key.
  - Built-in neural gateway fallback ensuring zero downtime and 100% real translation results even without an upfront paid key.
- **🔄 Smart Language & Text Swap**:
  - 180° animated swap button.
  - Seamlessly swaps languages and existing text for continuous conversation flow.
- **📋 One-Click Copy & Clear**:
  - Copy translated text to clipboard with instant visual feedback badge ("Copied!").
  - Quick clear button to reset input and output.
- **🔊 Text-to-Speech (Listen)**: Pronounce both source and translated text using the browser Speech Synthesis API.
- **⏳ Polished Loading Shimmer**: Pulsating wave skeleton shimmer and spinner animation during translation.
- **⚠️ Robust Error Handling**: Clean toast alerts for empty inputs, character limits, invalid language codes, and network exceptions.
- **⌨️ Keyboard Shortcuts**:
  - `Ctrl + Enter` (or `Cmd + Enter`): Instantly trigger translation.
  - `Alt + S`: Swap languages.
- **🔒 Secure Backend Proxy**: All translation requests are processed through the Flask backend (`/api/translate`); no secret API keys or third-party URLs are exposed to the client.

---

## 🏗️ Project Architecture

```
language-translator/
├── .env                       # Environment configuration file
├── .env.example               # Template for environment variables
├── .gitignore                 # Files excluded from version control
├── requirements.txt           # Python package dependencies
├── README.md                  # Detailed documentation and setup guide
├── run.py                     # Application startup entry point
├── app/
│   ├── __init__.py            # Flask application factory
│   ├── config.py              # Centralized environment configuration
│   ├── routes.py              # Web and API routing endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   └── translator.py      # Core translation engine (LibreTranslate + Neural Fallback)
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css      # Blue/purple gradient theme, glassmorphism, responsive rules
│   │   └── js/
│   │       └── app.js         # Frontend controller (AJAX, TTS, clipboard, DOM manipulation)
│   └── templates/
│       └── index.html         # Accessible HTML5 template
└── tests/
    └── test_translator.py     # Comprehensive automated test suite
```

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.9+ (Python 3.12 recommended)
- `pip` package manager

### 1. Clone or Open Project
Navigate to the project root directory:
```bash
cd language-translator
```

### 2. (Optional) Create a Virtual Environment
```bash
# On Windows
py -m venv .venv
.venv\Scripts\activate

# On macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
py -m pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
# Windows PowerShell
Copy-Item .env.example .env

# Bash / Linux
cp .env.example .env
```

Open `.env` to configure your preferences:
```ini
# Flask Server Settings
FLASK_ENV=development
FLASK_DEBUG=True
PORT=5000
SECRET_KEY=your-secret-key-here

# Translation Provider Options:
# 'auto'            -> Tries LibreTranslate if configured; falls back to Neural Gateway
# 'libretranslate'  -> Uses LibreTranslate API
TRANSLATION_PROVIDER=auto

# LibreTranslate Endpoint (Optional: specify your custom host or API key)
# For local Docker instance: http://localhost:5000
LIBRETRANSLATE_URL=https://libretranslate.com
LIBRETRANSLATE_API_KEY=
```

### 5. Run the Application
```bash
py run.py
```
Open your web browser and visit:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🐳 Optional: Running a Local LibreTranslate Instance

If you prefer to run a completely self-hosted, offline LibreTranslate instance using Docker:

```bash
docker run -ti --rm -p 5001:5000 libretranslate/libretranslate
```

Then simply update your `.env` file:
```ini
TRANSLATION_PROVIDER=libretranslate
LIBRETRANSLATE_URL=http://localhost:5001
LIBRETRANSLATE_API_KEY=
```
The application will immediately route all translations through your private local container!

---

## 🧪 Running Automated Tests

Run the full test suite covering input validation, error handling, route contracts, auto-detection, and real translation output across English, Tamil, Hindi, Spanish, French, and German:

```bash
py -m unittest tests/test_translator.py
```

Expected output:
```text
..............
----------------------------------------------------------------------
Ran 14 tests in 2.673s

OK
```

---

## 📡 API Reference

### 1. List Supported Languages
- **Endpoint**: `GET /api/languages`
- **Response**:
```json
{
  "success": true,
  "data": {
    "sources": [
      { "code": "auto", "flag": "🌐", "name": "Auto-detect", "native": "Detect language" },
      { "code": "en", "flag": "🇺🇸", "name": "English", "native": "English" },
      { "code": "ta", "flag": "🇮🇳", "name": "Tamil", "native": "தமிழ்" },
      { "code": "hi", "flag": "🇮🇳", "name": "Hindi", "native": "हिन्दी" }
    ],
    "targets": [
      { "code": "en", "flag": "🇺🇸", "name": "English", "native": "English" },
      { "code": "es", "flag": "🇪🇸", "name": "Spanish", "native": "Español" }
    ]
  }
}
```

### 2. Translate Text
- **Endpoint**: `POST /api/translate`
- **Headers**: `Content-Type: application/json`
- **Request Body**:
```json
{
  "text": "Good morning, how are you?",
  "source": "auto",
  "target": "ta"
}
```
- **Success Response** (`200 OK`):
```json
{
  "success": true,
  "data": {
    "translatedText": "காலை வணக்கம், எப்படி இருக்கிறீர்கள்?",
    "sourceLanguage": "auto",
    "targetLanguage": "ta",
    "detectedLanguage": "en",
    "detectedLanguageName": "English",
    "provider": "Google Gateway"
  }
}
```
- **Error Response** (`400 Bad Request`):
```json
{
  "success": false,
  "error": "Input text cannot be empty."
}
```

### 3. Service Health Check
- **Endpoint**: `GET /health`
- **Response**:
```json
{
  "service": "Language Translation Tool",
  "status": "healthy",
  "version": "1.0.0"
}
```

---

## 🎨 UI Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| `Ctrl + Enter` (or `Cmd + Enter`) | Translate text |
| `Alt + S` | Swap source and target languages |

---

## 📄 License
MIT License. Created with Clean Architecture and Professional UX.
