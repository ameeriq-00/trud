"""
نموذج الجلسات - Session Tracking
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, nullable=False, comment="معرف الجلسة")
    
    # ربط مع الحساب والبروكسي
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True, comment="معرف الحساب")
    proxy_id = Column(Integer, ForeignKey("proxies.id"), nullable=True, comment="معرف البروكسي")
    
    # معلومات الطلب
    phone_number = Column(String(20), nullable=False, comment="رقم الهاتف")
    request_type = Column(String(20), default="single", comment="نوع الطلب")  # single, bulk
    
    # نتيجة الطلب
    status = Column(String(20), default="pending", comment="حالة الطلب")  # pending, success, failed, timeout
    response_data = Column(Text, nullable=True, comment="بيانات الاستجابة")
    error_message = Column(String(500), nullable=True, comment="رسالة الخطأ")
    
    # معلومات الأداء
    response_time = Column(Float, default=0.0, comment="وقت الاستجابة بالثواني")
    request_size = Column(Integer, default=0, comment="حجم الطلب بالبايت")
    response_size = Column(Integer, default=0, comment="حجم الاستجابة بالبايت")
    
    # معلومات إضافية
    ip_address = Column(String(50), nullable=True, comment="عنوان IP المستخدم")
    user_agent = Column(String(500), nullable=True, comment="User Agent")
    
    # معلومات النتيجة
    contact_found = Column(Boolean, default=False, comment="تم العثور على جهة اتصال")
    contact_name = Column(String(200), nullable=True, comment="اسم جهة الاتصال")
    carrier_name = Column(String(100), nullable=True, comment="اسم المشغل")
    country_code = Column(String(5), nullable=True, comment="رمز البلد")
    is_spam = Column(Boolean, default=False, comment="رقم مزعج")
    
    # تواريخ النظام
    started_at = Column(DateTime, server_default=func.now(), comment="وقت بدء الطلب")
    completed_at = Column(DateTime, nullable=True, comment="وقت انتهاء الطلب")
    created_at = Column(DateTime, server_default=func.now(), comment="تاريخ الإنشاء")
    
    # العلاقات
    account = relationship("Account", backref="sessions")
    proxy = relationship("Proxy", backref="sessions")
    
    def __repr__(self):
        return f"<Session(id={self.id}, phone='{self.phone_number}', status='{self.status}')>"
    
    def to_dict(self):
        """تحويل إلى قاموس"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "account_id": self.account_id,
            "proxy_id": self.proxy_id,
            "phone_number": self.phone_number,
            "request_type": self.request_type,
            "status": self.status,
            "error_message": self.error_message,
            "response_time": self.response_time,
            "request_size": self.request_size,
            "response_size": self.response_size,
            "ip_address": self.ip_address,
            "contact_found": self.contact_found,
            "contact_name": self.contact_name,
            "carrier_name": self.carrier_name,
            "country_code": self.country_code,
            "is_spam": self.is_spam,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    def mark_completed(self, success: bool = True, error_message: str = None):
        """تحديد انتهاء الجلسة"""
        from datetime import datetime
        
        self.completed_at = datetime.utcnow()
        self.status = "success" if success else "failed"
        if error_message:
            self.error_message = error_message
        
        # حساب وقت الاستجابة
        if self.started_at:
            delta = self.completed_at - self.started_at
            self.response_time = delta.total_seconds()