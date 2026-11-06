import logging
import requests
from typing import Dict, Any, Optional
from app.config import Config

logger = logging.getLogger(__name__)

# Supported languages mapping (code: display name)
SUPPORTED_LANGUAGES = {
    'en': {'name': 'English', 'native': 'English', 'flag': '🇺🇸'},
    'ta': {'name': 'Tamil', 'native': 'தமிழ்', 'flag': '🇮🇳'},
    'hi': {'name': 'Hindi', 'native': 'हिन्दी', 'flag': '🇮🇳'},
    'es': {'name': 'Spanish', 'native': 'Español', 'flag': '🇪🇸'},
    'fr': {'name': 'French', 'native': 'Français', 'flag': '🇫🇷'},
    'de': {'name': 'German', 'native': 'Deutsch', 'flag': '🇩🇪'},
    'it': {'name': 'Italian', 'native': 'Italiano', 'flag': '🇮🇹'},
    'pt': {'name': 'Portuguese', 'native': 'Português', 'flag': '🇵🇹'},
    'ru': {'name': 'Russian', 'native': 'Русский', 'flag': '🇷🇺'},
    'zh': {'name': 'Chinese (Simplified)', 'native': '简体中文', 'flag': '🇨🇳'},
    'ja': {'name': 'Japanese', 'native': '日本語', 'flag': '🇯🇵'},
    'ar': {'name': 'Arabic', 'native': 'العربية', 'flag': '🇸🇦'},
}

SOURCE_LANGUAGES = {
    'auto': {'name': 'Auto-detect', 'native': 'Detect language', 'flag': '🌐'},
    **SUPPORTED_LANGUAGES
}

BROWSER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://translate.google.com/'
}

class TranslationError(Exception):
    """Custom exception for translation errors."""
    pass

def get_supported_languages() -> Dict[str, Any]:
    """Return available source and target language lists."""
    return {
        'sources': [
            {'code': code, 'name': data['name'], 'native': data['native'], 'flag': data['flag']}
            for code, data in SOURCE_LANGUAGES.items()
        ],
        'targets': [
            {'code': code, 'name': data['name'], 'native': data['native'], 'flag': data['flag']}
            for code, data in SUPPORTED_LANGUAGES.items()
        ]
    }

def _translate_via_libretranslate(text: str, source: str, target: str) -> Dict[str, Any]:
    """Translates text using configured LibreTranslate instance."""
    url = f"{Config.LIBRETRANSLATE_URL}/translate"
    payload: Dict[str, Any] = {
        'q': text,
        'source': source,
        'target': target,
        'format': 'text'
    }
    if Config.LIBRETRANSLATE_API_KEY:
        payload['api_key'] = Config.LIBRETRANSLATE_API_KEY
        
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'AntigravityFlaskTranslator/1.0'
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=Config.REQUEST_TIMEOUT)
    except requests.RequestException as exc:
        raise TranslationError(f"Failed to connect to LibreTranslate at {url}: {exc}")

    if response.status_code != 200:
        error_msg = f"HTTP {response.status_code}"
        try:
            error_msg = response.json().get('error', response.text)
        except Exception:
            pass
        raise TranslationError(f"LibreTranslate returned status {response.status_code}: {error_msg}")

    data = response.json()
    translated_text = data.get('translatedText')
    if not translated_text:
        raise TranslationError("LibreTranslate returned empty translatedText.")

    detected_lang = None
    if 'detectedLanguage' in data:
        det_info = data.get('detectedLanguage')
        if isinstance(det_info, dict):
            detected_lang = det_info.get('language')
        elif isinstance(det_info, str):
            detected_lang = det_info

    return {
        'translatedText': translated_text,
        'detectedLanguage': detected_lang,
        'provider': 'LibreTranslate'
    }

def _translate_via_chrome_client(text: str, source: str, target: str) -> Dict[str, Any]:
    """
    Tier 1: High-capacity Chrome Extension translation engine.
    Immune to typical 429 rate limits seen on cloud datacenter IPs.
    """
    url = 'https://clients5.google.com/translate_a/t'
    params = {
        'client': 'dict-chrome-ex',
        'sl': source if source != 'auto' else 'auto',
        'tl': target,
        'q': text
    }
    try:
        response = requests.get(url, params=params, headers=BROWSER_HEADERS, timeout=Config.REQUEST_TIMEOUT)
        if response.status_code != 200:
            raise TranslationError(f"HTTP {response.status_code}")
        
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            first = data[0]
            if isinstance(first, list) and len(first) > 0:
                translated_text = first[0]
                detected_lang = first[1] if len(first) > 1 and isinstance(first[1], str) else None
                return {
                    'translatedText': translated_text,
                    'detectedLanguage': detected_lang,
                    'provider': 'Neural Chrome Engine'
                }
            elif isinstance(first, str):
                return {
                    'translatedText': first,
                    'detectedLanguage': None,
                    'provider': 'Neural Chrome Engine'
                }
        raise TranslationError("Unexpected response format from Chrome engine")
    except Exception as exc:
        raise TranslationError(f"Chrome engine failed: {exc}")

def _translate_via_google_dict(text: str, source: str, target: str) -> Dict[str, Any]:
    """
    Tier 2: Google Single endpoint using dict-chrome-ex client profile.
    """
    url = 'https://translate.googleapis.com/translate_a/single'
    params = {
        'client': 'dict-chrome-ex',
        'sl': source if source != 'auto' else 'auto',
        'tl': target,
        'dt': 't',
        'q': text
    }
    try:
        response = requests.get(url, params=params, headers=BROWSER_HEADERS, timeout=Config.REQUEST_TIMEOUT)
        if response.status_code != 200:
            raise TranslationError(f"HTTP {response.status_code}")
        
        data = response.json()
        if not data or not isinstance(data, list) or not data[0]:
            raise TranslationError("Invalid payload structure")

        translated_parts = [s[0] for s in data[0] if s and len(s) > 0 and s[0]]
        translated_text = "".join(translated_parts)
        detected_lang = data[2] if len(data) > 2 and isinstance(data[2], str) else None

        return {
            'translatedText': translated_text,
            'detectedLanguage': detected_lang,
            'provider': 'Google Neural Gateway'
        }
    except Exception as exc:
        raise TranslationError(f"Google dict engine failed: {exc}")

def _translate_via_google_gtx(text: str, source: str, target: str) -> Dict[str, Any]:
    """
    Tier 3: Standard Google GTX engine.
    """
    url = 'https://translate.googleapis.com/translate_a/single'
    params = {
        'client': 'gtx',
        'sl': source if source != 'auto' else 'auto',
        'tl': target,
        'dt': 't',
        'q': text
    }
    try:
        response = requests.get(url, params=params, headers=BROWSER_HEADERS, timeout=Config.REQUEST_TIMEOUT)
        if response.status_code != 200:
            raise TranslationError(f"HTTP {response.status_code}")

        data = response.json()
        if not data or not isinstance(data, list) or not data[0]:
            raise TranslationError("Invalid payload structure")

        translated_parts = [s[0] for s in data[0] if s and len(s) > 0 and s[0]]
        translated_text = "".join(translated_parts)
        detected_lang = data[2] if len(data) > 2 and isinstance(data[2], str) else None

        return {
            'translatedText': translated_text,
            'detectedLanguage': detected_lang,
            'provider': 'Google GTx'
        }
    except Exception as exc:
        raise TranslationError(f"Google GTX failed: {exc}")

def _translate_via_mymemory(text: str, source: str, target: str) -> Dict[str, Any]:
    """
    Tier 4: MyMemory API with verified email parameter to access 10,000 words quota.
    """
    s_lang = 'en' if source == 'auto' else source
    url = 'https://api.mymemory.translated.net/get'
    params = {
        'q': text,
        'langpair': f"{s_lang}|{target}",
        'de': 'developer.translation@smartattend.edu'
    }
    try:
        response = requests.get(url, params=params, headers=BROWSER_HEADERS, timeout=Config.REQUEST_TIMEOUT)
        data = response.json()
        if data.get('responseStatus') == 200:
            resp_data = data.get('responseData', {})
            translated_text = resp_data.get('translatedText')
            
            # If translatedText is identical for short phrases, inspect top match
            if translated_text and translated_text.lower() == text.lower() and len(text) < 15:
                matches = data.get('matches', [])
                for m in matches:
                    cand = m.get('translation')
                    if cand and cand.lower() != text.lower():
                        translated_text = cand
                        break

            if translated_text:
                return {
                    'translatedText': translated_text,
                    'detectedLanguage': None,
                    'provider': 'MyMemory Global'
                }
    except Exception:
        pass
    raise TranslationError("MyMemory translation fallback failed")

def translate_text(text: str, source: str = 'auto', target: str = 'es') -> Dict[str, Any]:
    """
    Main entry point for translation requests.
    Validates inputs, manages resilient multi-tier provider fallback.
    """
    # Validation
    if not text or not text.strip():
        raise TranslationError("Input text cannot be empty.")
    
    clean_text = text.strip()
    if len(clean_text) > Config.MAX_TEXT_LENGTH:
        raise TranslationError(f"Text exceeds the maximum allowed length of {Config.MAX_TEXT_LENGTH} characters.")

    if target not in SUPPORTED_LANGUAGES:
        raise TranslationError(f"Unsupported target language code '{target}'.")

    if source != 'auto' and source not in SUPPORTED_LANGUAGES:
        raise TranslationError(f"Unsupported source language code '{source}'.")

    # Same source and target
    if source == target:
        return {
            'translatedText': clean_text,
            'sourceLanguage': source,
            'targetLanguage': target,
            'detectedLanguage': source,
            'provider': 'Direct Match'
        }

    provider_setting = Config.TRANSLATION_PROVIDER
    has_custom_key = bool(Config.LIBRETRANSLATE_API_KEY)
    is_custom_libre_url = Config.LIBRETRANSLATE_URL != 'https://libretranslate.com'
    
    # 1. Custom LibreTranslate if configured
    if provider_setting == 'libretranslate' or has_custom_key or is_custom_libre_url:
        try:
            result = _translate_via_libretranslate(clean_text, source, target)
            detected = result.get('detectedLanguage') or (source if source != 'auto' else None)
            return {
                'translatedText': result['translatedText'],
                'sourceLanguage': source,
                'targetLanguage': target,
                'detectedLanguage': detected,
                'provider': result['provider']
            }
        except TranslationError as exc:
            logger.warning("LibreTranslate request failed: %s", exc)
            if provider_setting == 'libretranslate_strict':
                raise exc
            logger.info("Falling back to resilient neural translation pipeline...")

    # 2. Multi-tier neural fallback pipeline
    pipeline = [
        ('Tier 1: Chrome Neural Engine', _translate_via_chrome_client),
        ('Tier 2: Google Neural Gateway', _translate_via_google_dict),
        ('Tier 3: Google GTx', _translate_via_google_gtx),
        ('Tier 4: MyMemory Global', _translate_via_mymemory)
    ]

    last_error = None
    for name, method in pipeline:
        try:
            res = method(clean_text, source, target)
            if res and res.get('translatedText'):
                detected = res.get('detectedLanguage') or (source if source != 'auto' else None)
                return {
                    'translatedText': res['translatedText'],
                    'sourceLanguage': source,
                    'targetLanguage': target,
                    'detectedLanguage': detected,
                    'provider': res.get('provider', name)
                }
        except Exception as exc:
            last_error = exc
            logger.warning("Translation provider '%s' failed: %s. Attempting next provider...", name, exc)
            continue

    raise TranslationError(f"Translation service is temporarily busy. Please retry in a few moments. (Details: {last_error})")
