"""
نموذج مفاتيح API - API Keys Model
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from datetime import datetime, timedelta
from app.core.database import Base


class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="اسم المفتاح")
    key = Column(String(255), unique=True, nullable=False, index=True, comment="المفتاح")
    description = Column(Text, nullable=True, comment="وصف المفتاح")
    
    # إعدادات الصلاحية
    is_active = Column(Boolean, default=True, comment="نشط")
    expires_at = Column(DateTime, nullable=True, comment="تاريخ انتهاء الصلاحية")
    
    # إحصائيات الاستخدام
    usage_count = Column(Integer, default=0, comment="عدد مرات الاستخدام")
    last_used = Column(DateTime, nullable=True, comment="آخر استخدام")
    
    # معلومات إضافية
    created_by = Column(String(100), nullable=True, comment="من أنشأه")
    notes = Column(Text, nullable=True, comment="ملاحظات")
    
    # تواريخ النظام
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="تاريخ الإنشاء")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="تاريخ التحديث")
    
    def __repr__(self):
        return f"<APIKey {self.name}: {self.key[:10]}...>"
    
    @property
    def is_expired(self) -> bool:
        """هل انتهت صلاحية المفتاح"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """هل المفتاح صالح للاستخدام"""
        return self.is_active and not self.is_expired
    
    @property
    def days_until_expiry(self) -> int:
        """عدد الأيام المتبقية لانتهاء الصلاحية"""
        if not self.expires_at:
            return -1  # لا ينتهي
        
        delta = self.expires_at - datetime.utcnow()
        return max(0, delta.days)
    
    def extend_expiry(self, days: int = 30):
        """تمديد صلاحية المفتاح"""
        if self.expires_at:
            self.expires_at += timedelta(days=days)
        else:
            self.expires_at = datetime.utcnow() + timedelta(days=days)
    
    def revoke(self):
        """إلغاء المفتاح"""
        self.is_active = False
    
    def to_dict(self) -> dict:
        """تحويل إلى قاموس"""
        return {
            "id": self.id,
            "name": self.name,
            "key": f"{self.key[:10]}..." if self.key else None,
            "description": self.description,
            "is_active": self.is_active,
            "is_expired": self.is_expired,
            "is_valid": self.is_valid,
            "usage_count": self.usage_count,
            "days_until_expiry": self.days_until_expiry,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }