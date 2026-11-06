import logging
import requests
from typing import Dict, Any, Optional
from app.config import Config

logger = logging.getLogger(__name__)

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
    """
    Translates text using LibreTranslate API endpoint.
    Respects LIBRETRANSLATE_URL and optional LIBRETRANSLATE_API_KEY from config.
    """
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
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=Config.REQUEST_TIMEOUT
        )
    except requests.RequestException as exc:
        raise TranslationError(f"Failed to connect to LibreTranslate at {url}: {exc}")

    if response.status_code != 200:
        error_msg = 'LibreTranslate error'
        try:
            err_json = response.json()
            error_msg = err_json.get('error', response.text)
        except Exception:
            error_msg = response.text or f"HTTP {response.status_code}"
        raise TranslationError(f"LibreTranslate returned status {response.status_code}: {error_msg}")

    data = response.json()
    translated_text = data.get('translatedText')
    if not translated_text:
        raise TranslationError("LibreTranslate returned empty translatedText.")

    detected_lang = None
    if 'detectedLanguage' in data:
        detected_lang_info = data.get('detectedLanguage')
        if isinstance(detected_lang_info, dict):
            detected_lang = detected_lang_info.get('language')
        elif isinstance(detected_lang_info, str):
            detected_lang = detected_lang_info

    return {
        'translatedText': translated_text,
        'detectedLanguage': detected_lang,
        'provider': 'LibreTranslate'
    }

def _translate_via_google_gtx(text: str, source: str, target: str) -> Dict[str, Any]:
    """
    High-reliability translation engine using Google GTx neural API.
    Used for seamless fallback or when configured as provider.
    """
    url = 'https://translate.googleapis.com/translate_a/single'
    params = {
        'client': 'gtx',
        'sl': source if source != 'auto' else 'auto',
        'tl': target,
        'dt': 't',
        'q': text
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': '*/*'
    }

    try:
        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=Config.REQUEST_TIMEOUT
        )
    except requests.RequestException as exc:
        raise TranslationError(f"Failed to connect to translation gateway: {exc}")

    if response.status_code != 200:
        raise TranslationError(f"Translation gateway error: HTTP {response.status_code}")

    try:
        res_data = response.json()
    except Exception as exc:
        raise TranslationError(f"Failed to parse translation response: {exc}")

    if not res_data or not isinstance(res_data, list) or not res_data[0]:
        raise TranslationError("Invalid translation payload structure.")

    # Combine all translated sentences/chunks
    translated_parts = []
    for sentence in res_data[0]:
        if sentence and len(sentence) > 0 and sentence[0]:
            translated_parts.append(sentence[0])

    translated_text = "".join(translated_parts)
    detected_lang = res_data[2] if len(res_data) > 2 and isinstance(res_data[2], str) else None

    return {
        'translatedText': translated_text,
        'detectedLanguage': detected_lang,
        'provider': 'Google Gateway'
    }

def _translate_via_mymemory(text: str, source: str, target: str) -> Dict[str, Any]:
    """
    Secondary fallback using MyMemory API.
    """
    s_lang = 'en' if source == 'auto' else source
    url = 'https://api.mymemory.translated.net/get'
    params = {
        'q': text,
        'langpair': f"{s_lang}|{target}"
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) LanguageTranslatorApp/1.0'
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=Config.REQUEST_TIMEOUT)
        data = response.json()
        if data.get('responseStatus') == 200:
            translated_text = data.get('responseData', {}).get('translatedText')
            if translated_text:
                return {
                    'translatedText': translated_text,
                    'detectedLanguage': None,
                    'provider': 'MyMemory'
                }
    except Exception:
        pass
    raise TranslationError("MyMemory translation fallback failed.")

def translate_text(text: str, source: str = 'auto', target: str = 'es') -> Dict[str, Any]:
    """
    Main entry point for translation requests.
    Validates inputs, manages provider selection and fallback mechanisms.
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
    
    # If explicitly set to libretranslate or user provided an API key/custom URL:
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
            logger.info("Falling back to neural translation gateway...")

    # Primary reliable neural translation (Google GTx)
    try:
        result = _translate_via_google_gtx(clean_text, source, target)
        detected = result.get('detectedLanguage') or (source if source != 'auto' else None)
        return {
            'translatedText': result['translatedText'],
            'sourceLanguage': source,
            'targetLanguage': target,
            'detectedLanguage': detected,
            'provider': result['provider']
        }
    except TranslationError as exc_primary:
        logger.warning("Primary neural gateway failed: %s. Attempting MyMemory fallback...", exc_primary)
        try:
            result = _translate_via_mymemory(clean_text, source, target)
            return {
                'translatedText': result['translatedText'],
                'sourceLanguage': source,
                'targetLanguage': target,
                'detectedLanguage': source if source != 'auto' else None,
                'provider': result['provider']
            }
        except Exception:
            raise TranslationError(f"All translation providers failed. Reason: {exc_primary}")
