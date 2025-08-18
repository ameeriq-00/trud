"""
إعدادات قاعدة البيانات - مُصححة
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from .config import settings
import logging

logger = logging.getLogger(__name__)

# إنشاء محرك قاعدة البيانات
engine = create_engine(
    settings.DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=settings.DEBUG  # إظهار SQL queries في وضع التطوير
)

# إنشاء جلسة قاعدة البيانات
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# القاعدة للنماذج
Base = declarative_base()


def get_db() -> Session:
    """الحصول على جلسة قاعدة بيانات"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """إنشاء قاعدة البيانات والجداول"""
    try:
        # استيراد جميع النماذج لضمان إنشاء الجداول
        from app.models import Base, Account, Proxy, Session as SessionModel, APIKey
        
        # إنشاء الجداول
        Base.metadata.create_all(bind=engine)
        
        # إنشاء بيانات افتراضية
        create_default_data()
        
        logger.info("✅ تم إنشاء قاعدة البيانات بنجاح")
        
    except Exception as e:
        logger.error(f"❌ خطأ في إنشاء قاعدة البيانات: {str(e)}")
        raise


def create_default_data():
    """إنشاء بيانات افتراضية"""
    try:
        from app.models.api_key import APIKey
        from app.core.security import create_api_key
        
        db = SessionLocal()
        
        # التحقق من وجود API key افتراضي
        existing_key = db.query(APIKey).filter(APIKey.name == "default").first()
        
        if not existing_key:
            # إنشاء API key افتراضي
            default_key = create_api_key()
            
            api_key = APIKey(
                name="default",
                key=default_key,
                description="مفتاح API افتراضي للاختبار",
                created_by="system",
                is_active=True
            )
            
            db.add(api_key)
            db.commit()
            
            logger.info(f"✅ تم إنشاء API Key افتراضي: {default_key}")
            
        db.close()
        
    except Exception as e:
        logger.error(f"❌ خطأ في إنشاء البيانات الافتراضية: {str(e)}")


def drop_all_tables():
    """حذف جميع الجداول - للاختبار فقط"""
    from app.models import Base
    Base.metadata.drop_all(bind=engine)
    logger.info("🗑️ تم حذف جميع الجداول")


def reset_database():
    """إعادة تعيين قاعدة البيانات"""
    drop_all_tables()
    init_db()
    logger.info("🔄 تم إعادة تعيين قاعدة البيانات")