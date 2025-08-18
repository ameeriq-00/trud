"""
نموذج الجلسات - Session Model محسن
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from app.core.database import Base


class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(50), unique=True, nullable=False, index=True, comment="معرف الجلسة الفريد")
    
    # معلومات الطلب
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True, comment="معرف الحساب المستخدم")
    proxy_id = Column(Integer, ForeignKey("proxies.id"), nullable=True, comment="معرف البروكسي المستخدم")
    phone_number = Column(String(20), nullable=False, index=True, comment="رقم الهاتف")
    request_type = Column(String(20), default="single", comment="نوع الطلب")
    
    # حالة الطلب
    status = Column(String(20), default="pending", comment="حالة الطلب")  # pending, completed, failed
    error_message = Column(Text, nullable=True, comment="رسالة الخطأ")
    
    # معلومات الأداء
    response_time = Column(Float, default=0.0, comment="وقت الاستجابة بالثواني")
    started_at = Column(DateTime, nullable=True, comment="وقت بدء الطلب")
    completed_at = Column(DateTime, nullable=True, comment="وقت انتهاء الطلب")
    
    # نتائج البحث
    contact_found = Column(Boolean, default=False, comment="تم العثور على جهة اتصال")
    contact_name = Column(String(100), nullable=True, comment="اسم جهة الاتصال")
    carrier_name = Column(String(50), nullable=True, comment="اسم المشغل")
    country_code = Column(String(10), nullable=True, comment="رمز البلد")
    is_spam = Column(Boolean, default=False, comment="مكالمة مزعجة")
    
    # معلومات إضافية
    user_agent = Column(String(200), nullable=True, comment="User Agent المستخدم")
    ip_address = Column(String(45), nullable=True, comment="عنوان IP")
    payload_used = Column(Text, nullable=True, comment="الـ Payload المستخدم")
    
    # تواريخ النظام
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="تاريخ الإنشاء")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="تاريخ التحديث")
    
    # العلاقات
    account = relationship("Account", back_populates="sessions")
    proxy = relationship("Proxy", back_populates="sessions")
    
    def __repr__(self):
        return f"<Session {self.session_id}: {self.phone_number} - {self.status}>"
    
    @property
    def duration(self) -> float:
        """حساب مدة الجلسة"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return 0.0
    
    @property
    def success_rate(self) -> float:
        """معدل نجاح الجلسة (0 أو 100)"""
        return 100.0 if self.status == "completed" and self.contact_found else 0.0
    
    def to_dict(self) -> dict:
        """تحويل إلى قاموس للتصدير"""
        return {
            "session_id": self.session_id,
            "phone_number": self.phone_number,
            "account_id": self.account_id,
            "proxy_id": self.proxy_id,
            "request_type": self.request_type,
            "status": self.status,
            "error_message": self.error_message,
            "response_time": self.response_time,
            "contact_found": self.contact_found,
            "contact_name": self.contact_name,
            "carrier_name": self.carrier_name,
            "country_code": self.country_code,
            "is_spam": self.is_spam,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "duration": self.duration
        }
    
    def mark_as_completed(self, contact_info: dict = None):
        """تمييز الجلسة كمكتملة"""
        self.status = "completed"
        self.completed_at = datetime.utcnow()
        
        if contact_info:
            self.contact_found = True
            self.contact_name = contact_info.get("name")
            self.carrier_name = contact_info.get("carrier")
            self.country_code = contact_info.get("country_code")
            self.is_spam = contact_info.get("is_spam", False)
        else:
            self.contact_found = False
    
    def mark_as_failed(self, error_message: str):
        """تمييز الجلسة كفاشلة"""
        self.status = "failed"
        self.error_message = error_message
        self.completed_at = datetime.utcnow()
        self.contact_found = False