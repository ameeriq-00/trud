"""
نظام الأمان والتشفير - مُصحح من خطأ NoneType
"""
from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Security, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .config import settings
from .database import get_db

# إعداد تشفير كلمات المرور
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# إعداد نظام التوثيق
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """التحقق من كلمة المرور"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """تشفير كلمة المرور"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """إنشاء JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """التحقق من صحة Token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError:
        return None


async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    """الحصول على المستخدم الحالي من Token"""
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload


def check_admin_credentials(username: str, password: str) -> bool:
    """التحقق من بيانات المشرف"""
    return (
        username == settings.ADMIN_USERNAME and 
        password == settings.ADMIN_PASSWORD
    )


class APIKeyAuth:
    """نظام التحقق من API Keys"""
    
    def __init__(self):
        self.security = HTTPBearer()
    
    async def __call__(
        self, 
        credentials: HTTPAuthorizationCredentials = Security(security),
        db: Session = Depends(get_db)
    ):
        """التحقق من صحة API Key"""
        from app.models.api_key import APIKey
        
        api_key_value = credentials.credentials
        
        # البحث عن API Key في قاعدة البيانات
        api_key = db.query(APIKey).filter(
            APIKey.key == api_key_value,
            APIKey.is_active == True
        ).first()
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # فحص انتهاء الصلاحية
        if api_key.expires_at and datetime.utcnow() > api_key.expires_at:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # تحديث آخر استخدام - مع التعامل مع NoneType
        api_key.last_used = datetime.utcnow()
        
        # التعامل مع usage_count إذا كان None
        if api_key.usage_count is None:
            api_key.usage_count = 0
        api_key.usage_count += 1
        
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"خطأ في تحديث API key: {str(e)}")
        
        return api_key


async def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
):
    """التحقق من صحة API Key - دالة مساعدة"""
    api_key_auth = APIKeyAuth()
    return await api_key_auth(credentials, db)


def create_api_key() -> str:
    """إنشاء API key جديد"""
    import secrets
    import string
    
    # إنشاء مفتاح عشوائي بطول 32 حرف
    alphabet = string.ascii_letters + string.digits
    api_key = ''.join(secrets.choice(alphabet) for _ in range(32))
    
    return f"hc_{api_key}"


def hash_api_key(api_key: str) -> str:
    """تشفير API key للحفظ في قاعدة البيانات"""
    return get_password_hash(api_key)


def verify_api_key_hash(api_key: str, hashed_key: str) -> bool:
    """التحقق من API key مقابل الهاش المحفوظ"""
    return verify_password(api_key, hashed_key)