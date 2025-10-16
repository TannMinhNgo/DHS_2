import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Flask cơ bản
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or f"sqlite:///{os.path.join(BASE_DIR,'app.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload settings
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB max file size
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'images')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # Security
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    
    # Rate limiting
    RATELIMIT_STORAGE_URL = "memory://"
    RATELIMIT_DEFAULT = "200 per day, 50 per hour"
    
    # Logging
    LOG_LEVEL = "INFO"
    
    # Pagination
    POSTS_PER_PAGE = 20
    LAPTOPS_PER_PAGE = 20
    
    # AI Chatbot
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "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")
    CHATBOT_MAX_TOKENS = 1000
    CHATBOT_TEMPERATURE = 0.7