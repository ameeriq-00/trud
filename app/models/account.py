"""
نموذج الحسابات - HelloCallers Accounts
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float
from sqlalchemy.sql import func
from app.core.database import Base


class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="اسم الحساب")
    token = Column(Text, nullable=False, comment="JWT Token")
    device_id = Column(String(100), nullable=False, comment="معرف الجهاز")
    player_id = Column(String(100), nullable=False, comment="معرف المشغل")
    user_agent = Column(String(500), nullable=True, comment="User Agent")
    
    # إحصائيات الاستخدام
    request_count = Column(Integer, default=0, comment="عدد الطلبات")
    successful_requests = Column(Integer, default=0, comment="الطلبات الناجحة")
    failed_requests = Column(Integer, default=0, comment="الطلبات الفاشلة")
    last_used = Column(DateTime, nullable=True, comment="آخر استخدام")
    
    # إعدادات Rate Limiting
    rate_limit = Column(Integer, default=50, comment="حد الطلبات في الساعة")
    current_hour_requests = Column(Integer, default=0, comment="طلبات الساعة الحالية")
    hour_reset_time = Column(DateTime, nullable=True, comment="وقت إعادة تعيين العداد")
    
    # حالة الحساب
    is_active = Column(Boolean, default=True, comment="نشط")
    is_banned = Column(Boolean, default=False, comment="محظور")
    ban_reason = Column(String(500), nullable=True, comment="سبب الحظر")
    
    # معلومات إضافية
    country = Column(String(5), default="IQ", comment="البلد")
    locale = Column(String(10), default="ar", comment="اللغة")
    notes = Column(Text, nullable=True, comment="ملاحظات")
    
    # تواريخ النظام
    created_at = Column(DateTime, server_default=func.now(), comment="تاريخ الإنشاء")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="تاريخ التحديث")
    
    def __repr__(self):
        return f"<Account(id={self.id}, name='{self.name}', active={self.is_active})>"
    
    def to_dict(self):
        """تحويل إلى قاموس"""
        return {
            "id": self.id,
            "name": self.name,
            "device_id": self.device_id,
            "player_id": self.player_id,
            "request_count": self.request_count,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "rate_limit": self.rate_limit,
            "current_hour_requests": self.current_hour_requests,
            "is_active": self.is_active,
            "is_banned": self.is_banned,
            "ban_reason": self.ban_reason,
            "country": self.country,
            "locale": self.locale,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @property
    def remaining_requests(self):
        """الطلبات المتبقية في الساعة"""
        return max(0, self.rate_limit - self.current_hour_requests)
    
    @property
    def success_rate(self):
        """معدل نجاح الطلبات"""
        if self.request_count == 0:
            return 0.0
        return (self.successful_requests / self.request_count) * 100
    
    def can_make_request(self):
        """هل يمكن للحساب إجراء طلب جديد؟"""
        if not self.is_active or self.is_banned:
            return False
        
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        
        # إعادة تعيين العداد إذا مر ساعة
        if (self.hour_reset_time is None or 
            now >= self.hour_reset_time + timedelta(hours=1)):
            self.current_hour_requests = 0
            self.hour_reset_time = now
        
        return self.current_hour_requests < self.rate_limit
    
    def increment_request_count(self, success: bool = True):
        """زيادة عداد الطلبات"""
        from datetime import datetime
        
        self.request_count += 1
        self.current_hour_requests += 1
        self.last_used = datetime.utcnow()
        
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1