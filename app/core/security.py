"""
نظام الأمان والتشفير
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

async def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
):
    """التحقق من صحة API Key"""
    from app.models.api_key import APIKey
    
    api_key = credentials.credentials
    
    # البحث عن API Key في قاعدة البيانات
    db_api_key = db.query(APIKey).filter(
        APIKey.key == api_key,
        APIKey.is_active == True
    ).first()
    
    if not db_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # تحديث آخر استخدام
    db_api_key.last_used = datetime.utcnow()
    db_api_key.usage_count += 1
    db.commit()
    
    return db_api_key

def check_admin_credentials(username: str, password: str) -> bool:
    """التحقق من بيانات المدير"""
    return (username == settings.ADMIN_USERNAME and 
            password == settings.ADMIN_PASSWORD)

class APIKeyAuth:
    """نظام التحقق من API Key"""
    
    def __init__(self, auto_error: bool = True):
        self.auto_error = auto_error
    
    async def __call__(
        self, 
        credentials: HTTPAuthorizationCredentials = Security(security),
        db: Session = Depends(get_db)
    ):
        return await verify_api_key(credentials, db)