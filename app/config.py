import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-dev-secret-key-change-in-production')
    PORT = int(os.getenv('PORT', 5000))
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() in ('true', '1', 't')
    
    # Translation settings
    TRANSLATION_PROVIDER = os.getenv('TRANSLATION_PROVIDER', 'auto').strip().lower()
    LIBRETRANSLATE_URL = os.getenv('LIBRETRANSLATE_URL', 'https://libretranslate.com').rstrip('/')
    LIBRETRANSLATE_API_KEY = os.getenv('LIBRETRANSLATE_API_KEY', '').strip()
    
    # Constraints
    MAX_TEXT_LENGTH = 5000
    REQUEST_TIMEOUT = 12  # seconds
