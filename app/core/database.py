"""
إعداد قاعدة البيانات
"""
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from .config import settings

# إنشاء محرك قاعدة البيانات
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={
            "check_same_thread": False,
            "timeout": 20
        },
        poolclass=StaticPool,
        echo=settings.DEBUG
    )
else:
    engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG
    )

# إنشاء جلسة قاعدة البيانات
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class للجداول
Base = declarative_base()

# Metadata للجداول
metadata = MetaData()


def get_db():
    """
    الحصول على جلسة قاعدة البيانات
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    إنشاء جميع الجداول
    """
    # استيراد جميع النماذج هنا لضمان إنشاء الجداول
    from app.models.account import Account
    from app.models.proxy import Proxy
    from app.models.session import Session
    from app.models.api_key import APIKey
    
    Base.metadata.create_all(bind=engine)
    
    # إنشاء البيانات الافتراضية
    create_default_data()


def create_default_data():
    """
    إنشاء البيانات الافتراضية
    """
    from app.models.api_key import APIKey
    from app.core.security import get_password_hash
    
    db = SessionLocal()
    try:
        # إنشاء API key افتراضي للمدير
        admin_api_key = db.query(APIKey).filter(APIKey.name == "admin").first()
        if not admin_api_key:
            admin_api_key = APIKey(
                name="admin",
                key="trud-admin-key-12345",
                description="مفتاح المدير الافتراضي",
                is_active=True,
                created_by="system"
            )
            db.add(admin_api_key)
            db.commit()
            print(f"✅ تم إنشاء API Key: {admin_api_key.key}")
    
    except Exception as e:
        print(f"❌ خطأ في إنشاء البيانات الافتراضية: {e}")
        db.rollback()
    finally:
        db.close()