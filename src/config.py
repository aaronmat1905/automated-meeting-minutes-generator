"""
Configuration management for Meeting Minutes Generator
Loads environment variables and provides configuration objects
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
    FLASK_APP = os.getenv('FLASK_APP', 'src.app')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

    # Database Configuration
    DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{BASE_DIR}/meeting_minutes.db')
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Google Cloud Configuration
    GOOGLE_CLOUD_PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT_ID')
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

    # Gemini API Configuration
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-1.5-pro')
    GEMINI_TEMPERATURE = float(os.getenv('GEMINI_TEMPERATURE', '0.2'))
    GEMINI_MAX_OUTPUT_TOKENS = int(os.getenv('GEMINI_MAX_OUTPUT_TOKENS', '8192'))

    # Google Cloud Speech-to-Text Configuration
    GOOGLE_SPEECH_LANGUAGE_CODE = os.getenv('GOOGLE_SPEECH_LANGUAGE_CODE', 'en-US')
    GOOGLE_SPEECH_SAMPLE_RATE_HERTZ = int(os.getenv('GOOGLE_SPEECH_SAMPLE_RATE_HERTZ', '16000'))
    GOOGLE_SPEECH_ENCODING = os.getenv('GOOGLE_SPEECH_ENCODING', 'LINEAR16')
    GOOGLE_SPEECH_ENABLE_DIARIZATION = True
    GOOGLE_SPEECH_MAX_SPEAKER_COUNT = int(os.getenv('MAX_SPEAKERS', '8'))

    # Google Cloud Storage Configuration
    GCS_BUCKET_NAME = os.getenv('GCS_BUCKET_NAME')
    GCS_AUDIO_FOLDER = os.getenv('GCS_AUDIO_FOLDER', 'audio-files')
    GCS_TRANSCRIPTS_FOLDER = os.getenv('GCS_TRANSCRIPTS_FOLDER', 'transcripts')

    # Google Calendar Configuration
    GOOGLE_CALENDAR_ID = os.getenv('GOOGLE_CALENDAR_ID', 'primary')
    GOOGLE_CALENDAR_SCOPES = [
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/calendar.events'
    ]

    # Outlook/Microsoft 365 Calendar Configuration
    OUTLOOK_CLIENT_ID = os.getenv('OUTLOOK_CLIENT_ID')
    OUTLOOK_CLIENT_SECRET = os.getenv('OUTLOOK_CLIENT_SECRET')
    OUTLOOK_TENANT_ID = os.getenv('OUTLOOK_TENANT_ID', 'common')
    OUTLOOK_REDIRECT_URI = os.getenv('OUTLOOK_REDIRECT_URI', 'http://localhost:5000/callback')
    OUTLOOK_SCOPES = ['Calendars.ReadWrite', 'User.Read']

    # Application Settings
    MAX_AUDIO_FILE_SIZE_MB = int(os.getenv('MAX_AUDIO_FILE_SIZE_MB', '500'))
    MAX_AUDIO_FILE_SIZE_BYTES = MAX_AUDIO_FILE_SIZE_MB * 1024 * 1024
    ALLOWED_AUDIO_FORMATS = os.getenv('ALLOWED_AUDIO_FORMATS', 'mp3,wav,mp4,m4a,flac,ogg').split(',')
    TRANSCRIPTION_TIMEOUT_SECONDS = int(os.getenv('TRANSCRIPTION_TIMEOUT_SECONDS', '600'))

    # Export Settings
    EXPORT_FORMATS = os.getenv('EXPORT_FORMATS', 'pdf,markdown,txt,docx').split(',')
    PDF_FONT = os.getenv('PDF_FONT', 'Helvetica')
    PDF_FONT_SIZE = int(os.getenv('PDF_FONT_SIZE', '12'))

    # Redis Configuration (for Celery)
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL

    # Jira Integration
    JIRA_SERVER = os.getenv('JIRA_SERVER')
    JIRA_EMAIL = os.getenv('JIRA_EMAIL')
    JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')

    # Asana Integration
    ASANA_ACCESS_TOKEN = os.getenv('ASANA_ACCESS_TOKEN')
    ASANA_WORKSPACE_ID = os.getenv('ASANA_WORKSPACE_ID')

    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # Upload folder
    UPLOAD_FOLDER = BASE_DIR / 'data' / 'uploads'
    TRANSCRIPT_FOLDER = BASE_DIR / 'data' / 'transcripts'
    EXPORT_FOLDER = BASE_DIR / 'data' / 'exports'

    @staticmethod
    def init_app(app):
        """Initialize application with configuration"""
        # Create necessary directories
        Config.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        Config.TRANSCRIPT_FOLDER.mkdir(parents=True, exist_ok=True)
        Config.EXPORT_FOLDER.mkdir(parents=True, exist_ok=True)
        (BASE_DIR / 'logs').mkdir(exist_ok=True)


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    DATABASE_URL = 'sqlite:///:memory:'
    SQLALCHEMY_DATABASE_URI = DATABASE_URL


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(config_name=None):
    """Get configuration object based on environment"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    return config.get(config_name, DevelopmentConfig)
