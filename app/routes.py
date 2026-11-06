import logging
from flask import Blueprint, render_template, request, jsonify
from app.services.translator import (
    translate_text,
    get_supported_languages,
    TranslationError,
    SUPPORTED_LANGUAGES,
    SOURCE_LANGUAGES
)

logger = logging.getLogger(__name__)

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Render the main translator application page."""
    languages = get_supported_languages()
    return render_template(
        'index.html',
        source_languages=languages['sources'],
        target_languages=languages['targets']
    )

@bp.route('/api/languages', methods=['GET'])
def api_languages():
    """Return JSON list of supported source and target languages."""
    return jsonify({
        'success': True,
        'data': get_supported_languages()
    }), 200

@bp.route('/api/translate', methods=['POST'])
def api_translate():
    """
    Handle translation requests.
    Expects JSON body:
    {
        "text": "Text to translate",
        "source": "en" | "auto" (default: "auto"),
        "target": "es" (default: "es")
    }
    """
    if not request.is_json:
        return jsonify({
            'success': False,
            'error': 'Request content-type must be application/json.'
        }), 400

    data = request.get_json() or {}
    text = data.get('text', '')
    source = data.get('source', 'auto')
    target = data.get('target', 'es')

    if not text or not isinstance(text, str) or not text.strip():
        return jsonify({
            'success': False,
            'error': 'Please enter some text to translate.'
        }), 400

    if not target or target not in SUPPORTED_LANGUAGES:
        return jsonify({
            'success': False,
            'error': f'Invalid or unsupported target language: "{target}".'
        }), 400

    if source != 'auto' and source not in SUPPORTED_LANGUAGES:
        return jsonify({
            'success': False,
            'error': f'Invalid or unsupported source language: "{source}".'
        }), 400

    try:
        result = translate_text(text, source=source, target=target)
        
        # Enrich detected language display name if present
        detected_code = result.get('detectedLanguage')
        detected_name = None
        if detected_code and detected_code in SUPPORTED_LANGUAGES:
            detected_name = SUPPORTED_LANGUAGES[detected_code]['name']

        return jsonify({
            'success': True,
            'data': {
                'translatedText': result['translatedText'],
                'sourceLanguage': result['sourceLanguage'],
                'targetLanguage': result['targetLanguage'],
                'detectedLanguage': detected_code,
                'detectedLanguageName': detected_name,
                'provider': result.get('provider', 'Real Translation API')
            }
        }), 200

    except TranslationError as te:
        logger.warning("Translation failed: %s", te)
        return jsonify({
            'success': False,
            'error': str(te)
        }), 400
    except Exception as exc:
        logger.exception("Unexpected error during translation: %s", exc)
        return jsonify({
            'success': False,
            'error': 'An internal error occurred during translation. Please try again later.'
        }), 500

@bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'Language Translation Tool',
        'version': '1.0.0'
    }), 200
