"""
Simplified Configuration - No Google Cloud Required!
Only needs Gemini API key
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    """Base configuration class"""

    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

    # Gemini API Configuration
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-1.5-pro')
    GEMINI_TEMPERATURE = float(os.getenv('GEMINI_TEMPERATURE', '0.2'))
    GEMINI_MAX_OUTPUT_TOKENS = int(os.getenv('GEMINI_MAX_OUTPUT_TOKENS', '8192'))

    # AssemblyAI Configuration (Cloud Transcription - FREE tier)
    ASSEMBLYAI_API_KEY = os.getenv('ASSEMBLYAI_API_KEY')
    TRANSCRIPTION_LANGUAGE = os.getenv('TRANSCRIPTION_LANGUAGE', 'en')

    # Application Settings
    MAX_AUDIO_FILE_SIZE_MB = int(os.getenv('MAX_AUDIO_FILE_SIZE_MB', '100'))
    MAX_AUDIO_FILE_SIZE_BYTES = MAX_AUDIO_FILE_SIZE_MB * 1024 * 1024
    ALLOWED_AUDIO_FORMATS = os.getenv('ALLOWED_AUDIO_FORMATS', 'mp3,wav,mp4,m4a,flac,ogg,webm').split(',')

    # Export Settings
    EXPORT_FORMATS = os.getenv('EXPORT_FORMATS', 'pdf,markdown,txt,docx').split(',')
    PDF_FONT = os.getenv('PDF_FONT', 'Helvetica')
    PDF_FONT_SIZE = int(os.getenv('PDF_FONT_SIZE', '12'))

    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # Folders
    UPLOAD_FOLDER = BASE_DIR / 'data' / 'uploads'
    TRANSCRIPT_FOLDER = BASE_DIR / 'data' / 'transcripts'
    EXPORT_FOLDER = BASE_DIR / 'data' / 'exports'
    STATIC_FOLDER = BASE_DIR / 'src' / 'static'
    TEMPLATES_FOLDER = BASE_DIR / 'src' / 'templates'

    @staticmethod
    def init_app(app):
        """Initialize application with configuration"""
        # Create necessary directories
        Config.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        Config.TRANSCRIPT_FOLDER.mkdir(parents=True, exist_ok=True)
        Config.EXPORT_FOLDER.mkdir(parents=True, exist_ok=True)
        Config.STATIC_FOLDER.mkdir(parents=True, exist_ok=True)
        Config.TEMPLATES_FOLDER.mkdir(parents=True, exist_ok=True)
        (BASE_DIR / 'logs').mkdir(exist_ok=True)


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config(config_name=None):
    """Get configuration object based on environment"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    return config.get(config_name, DevelopmentConfig)
