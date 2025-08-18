"""
إعدادات المشروع الرئيسية
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    # معلومات المشروع
    PROJECT_NAME: str = "TRUD - HelloCallers Proxy"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # إعدادات قاعدة البيانات
    DATABASE_URL: str = "sqlite:///./data/database.db"
    
    # إعدادات الأمان
    SECRET_KEY: str = "your-super-secret-key-change-this-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"
    
    # إعدادات HelloCallers
    HELLOCALLERS_BASE_URL: str = "https://hellocallers.com"
    DEFAULT_RATE_LIMIT: int = 50
    REQUEST_TIMEOUT: int = 30
    
    # إعدادات الخادم
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # إعدادات Redis
    REDIS_URL: Optional[str] = None
    
    # إعدادات التسجيل
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# إنشاء كائن الإعدادات
settings = Settings()

# إنشاء مجلدات إذا لم تكن موجودة
os.makedirs("data", exist_ok=True)
os.makedirs("logs", exist_ok=True)
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)
os.makedirs("templates", exist_ok=True)