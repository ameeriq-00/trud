"""
نموذج مفاتيح API
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from app.core.database import Base


class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="اسم المفتاح")
    key = Column(String(255), unique=True, nullable=False, comment="المفتاح")
    description = Column(Text, nullable=True, comment="وصف المفتاح")
    
    # إحصائيات الاستخدام
    usage_count = Column(Integer, default=0, comment="عدد مرات الاستخدام")
    last_used = Column(DateTime, nullable=True, comment="آخر استخدام")
    
    # إعدادات
    rate_limit = Column(Integer, default=1000, comment="حد الطلبات في الساعة")
    allowed_ips = Column(Text, nullable=True, comment="عناوين IP المسموحة (مفصولة بفواصل)")
    
    # حالة المفتاح
    is_active = Column(Boolean, default=True, comment="نشط")
    expires_at = Column(DateTime, nullable=True, comment="تاريخ انتهاء الصلاحية")
    
    # معلومات المنشئ
    created_by = Column(String(100), nullable=True, comment="منشئ المفتاح")
    
    # تواريخ النظام
    created_at = Column(DateTime, server_default=func.now(), comment="تاريخ الإنشاء")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="تاريخ التحديث")
    
    def __repr__(self):
        return f"<APIKey(id={self.id}, name='{self.name}', active={self.is_active})>"
    
    def to_dict(self):
        """تحويل إلى قاموس"""
        return {
            "id": self.id,
            "name": self.name,
            "key": self.key,
            "description": self.description,
            "usage_count": self.usage_count,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "rate_limit": self.rate_limit,
            "allowed_ips": self.allowed_ips.split(",") if self.allowed_ips else [],
            "is_active": self.is_active,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def is_valid(self):
        """هل المفتاح صالح؟"""
        if not self.is_active:
            return False
        
        if self.expires_at:
            from datetime import datetime
            if datetime.utcnow() > self.expires_at:
                return False
        
        return True
    
    def is_ip_allowed(self, ip_address: str):
        """هل عنوان IP مسموح؟"""
        if not self.allowed_ips:
            return True  # إذا لم تحدد عناوين، فالكل مسموح
        
        allowed_list = [ip.strip() for ip in self.allowed_ips.split(",")]
        return ip_address in allowed_list