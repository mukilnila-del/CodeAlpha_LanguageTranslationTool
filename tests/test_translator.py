import unittest
import json
import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.services.translator import translate_text, get_supported_languages, TranslationError

class TranslatorTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()

    def test_get_supported_languages(self):
        langs = get_supported_languages()
        self.assertIn('sources', langs)
        self.assertIn('targets', langs)
        
        target_codes = [t['code'] for t in langs['targets']]
        # Verify required languages: English, Tamil, Hindi, French, German, Spanish
        for req in ['en', 'ta', 'hi', 'fr', 'de', 'es']:
            self.assertIn(req, target_codes, f"Language {req} must be present in targets")

        source_codes = [s['code'] for s in langs['sources']]
        self.assertIn('auto', source_codes, "Auto-detect must be in source languages")

    def test_direct_match(self):
        result = translate_text("Hello", source="en", target="en")
        self.assertEqual(result['translatedText'], "Hello")

    def test_empty_text_error(self):
        with self.assertRaises(TranslationError):
            translate_text("", source="en", target="es")

    def test_real_translation_spanish(self):
        result = translate_text("Hello, how are you?", source="en", target="es")
        self.assertIn('translatedText', result)
        self.assertTrue(len(result['translatedText']) > 0)
        self.assertIn('hola', result['translatedText'].lower())

    def test_real_translation_french(self):
        result = translate_text("Thank you very much", source="en", target="fr")
        self.assertIn('translatedText', result)
        self.assertTrue('merci' in result['translatedText'].lower())

    def test_real_translation_german(self):
        result = translate_text("Good morning", source="en", target="de")
        self.assertIn('translatedText', result)
        self.assertTrue('guten' in result['translatedText'].lower())

    def test_real_translation_tamil(self):
        result = translate_text("Good morning", source="en", target="ta")
        self.assertIn('translatedText', result)
        self.assertTrue(len(result['translatedText']) > 0)

    def test_real_translation_hindi(self):
        result = translate_text("Good morning", source="en", target="hi")
        self.assertIn('translatedText', result)
        self.assertTrue(len(result['translatedText']) > 0)

    def test_api_languages_endpoint(self):
        response = self.client.get('/api/languages')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn('targets', data['data'])

    def test_api_translate_success(self):
        payload = {
            'text': 'Good morning',
            'source': 'en',
            'target': 'es'
        }
        response = self.client.post('/api/translate', json=payload)
        self.assertEqual(response.status_code, 200)
        res_data = response.get_json()
        self.assertTrue(res_data['success'])
        self.assertIn('translatedText', res_data['data'])
        self.assertTrue(len(res_data['data']['translatedText']) > 0)
        self.assertIn('provider', res_data['data'])

    def test_api_translate_auto_detect(self):
        payload = {
            'text': 'Bonjour tout le monde',
            'source': 'auto',
            'target': 'en'
        }
        response = self.client.post('/api/translate', json=payload)
        self.assertEqual(response.status_code, 200)
        res_data = response.get_json()
        self.assertTrue(res_data['success'])
        self.assertIn('hello', res_data['data']['translatedText'].lower())

    def test_api_translate_empty_text(self):
        payload = {
            'text': '   ',
            'source': 'en',
            'target': 'es'
        }
        response = self.client.post('/api/translate', json=payload)
        self.assertEqual(response.status_code, 400)
        res_data = response.get_json()
        self.assertFalse(res_data['success'])
        self.assertIn('error', res_data)

    def test_api_translate_invalid_target(self):
        payload = {
            'text': 'Hello',
            'source': 'en',
            'target': 'invalid_lang_code'
        }
        response = self.client.post('/api/translate', json=payload)
        self.assertEqual(response.status_code, 400)
        res_data = response.get_json()
        self.assertFalse(res_data['success'])

    def test_index_route(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('PolyGlot', html)
        self.assertIn('Translate Now', html)

if __name__ == '__main__':
    unittest.main()
