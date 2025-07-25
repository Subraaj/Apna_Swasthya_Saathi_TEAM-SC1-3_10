import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Basic Flask Config
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'apna-swasthya-saathi-secret-key-2024'
    
    # Database Configuration
    SUPABASE_URL = os.environ.get('SUPABASE_URL') or 'https://your-project.supabase.co'
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY') or 'your-supabase-anon-key'
    SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY') or 'your-service-role-key'
    
    # PostgreSQL (Alternative to Supabase)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://username:password@localhost/apna_swasthya_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-string'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # AI/ML Configuration
    HUGGINGFACE_API_KEY = os.environ.get('HUGGINGFACE_API_KEY') or 'hf_your_token_here'
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY') or 'AIzaSyA17TYUA-SKvSUhVPh9EtKZWWyPyVQOp08'
    
    # Government APIs
    BSKY_API_URL = os.environ.get('BSKY_API_URL') or 'https://bsky.odisha.gov.in/api'
    ABDM_API_URL = os.environ.get('ABDM_API_URL') or 'https://dev.abdm.gov.in'
    COWIN_API_URL = os.environ.get('COWIN_API_URL') or 'https://cdn-api.co-vin.in/api'
    
    # Redis Configuration
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # Email Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # File Upload Configuration
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/1'
    
    # Demo Credentials
    DEMO_ASHA_EMAIL = 'asha@demo.com'
    DEMO_ASHA_PASSWORD = 'demo123'
    DEMO_CITIZEN_EMAIL = 'citizen@demo.com'
    DEMO_CITIZEN_PASSWORD = 'demo123'

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}