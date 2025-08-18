"""
نموذج الحسابات - HelloCallers Accounts مُصحح
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
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
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="تاريخ الإنشاء")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="تاريخ التحديث")
    
    # العلاقات - مُصححة
    sessions = relationship("Session", back_populates="account", lazy="dynamic")
    
    def __repr__(self):
        return f"<Account {self.name}: {self.device_id}>"
    
    @property
    def success_rate(self) -> float:
        """معدل النجاح"""
        if self.request_count == 0:
            return 0.0
        return (self.successful_requests / self.request_count) * 100
    
    @property
    def remaining_requests(self) -> int:
        """الطلبات المتبقية في الساعة الحالية"""
        return max(0, self.rate_limit - self.current_hour_requests)
    
    @property
    def is_rate_limited(self) -> bool:
        """هل وصل للحد الأقصى من الطلبات"""
        return self.current_hour_requests >= self.rate_limit
    
    def can_make_request(self) -> bool:
        """هل يمكن إجراء طلب جديد"""
        return (
            self.is_active and 
            not self.is_banned and 
            not self.is_rate_limited
        )
    
    def increment_request_count(self, success: bool = True):
        """زيادة عداد الطلبات"""
        self.request_count += 1
        self.current_hour_requests += 1
        self.last_used = datetime.utcnow()
        
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
    
    def reset_hourly_requests(self):
        """إعادة تعيين عداد الطلبات الساعي"""
        from datetime import timedelta
        self.current_hour_requests = 0
        self.hour_reset_time = datetime.utcnow() + timedelta(hours=1)
    
    def to_dict(self) -> dict:
        """تحويل إلى قاموس"""
        return {
            "id": self.id,
            "name": self.name,
            "device_id": self.device_id,
            "player_id": self.player_id,
            "request_count": self.request_count,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": self.success_rate,
            "rate_limit": self.rate_limit,
            "current_hour_requests": self.current_hour_requests,
            "remaining_requests": self.remaining_requests,
            "is_active": self.is_active,
            "is_banned": self.is_banned,
            "country": self.country,
            "locale": self.locale,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }