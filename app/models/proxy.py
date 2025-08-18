"""
نموذج البروكسي - Proxy Management
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float
from sqlalchemy.sql import func
from app.core.database import Base


class Proxy(Base):
    __tablename__ = "proxies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="اسم البروكسي")
    host = Column(String(255), nullable=False, comment="عنوان الخادم")
    port = Column(Integer, nullable=False, comment="المنفذ")
    username = Column(String(100), nullable=True, comment="اسم المستخدم")
    password = Column(String(100), nullable=True, comment="كلمة المرور")
    proxy_type = Column(String(20), default="http", comment="نوع البروكسي")  # http, https, socks4, socks5
    
    # معلومات الموقع
    country = Column(String(5), nullable=True, comment="البلد")
    city = Column(String(100), nullable=True, comment="المدينة")
    ip_address = Column(String(50), nullable=True, comment="عنوان IP الحقيقي")
    
    # إحصائيات الأداء
    total_requests = Column(Integer, default=0, comment="إجمالي الطلبات")
    successful_requests = Column(Integer, default=0, comment="الطلبات الناجحة")
    failed_requests = Column(Integer, default=0, comment="الطلبات الفاشلة")
    average_response_time = Column(Float, default=0.0, comment="متوسط وقت الاستجابة")
    last_used = Column(DateTime, nullable=True, comment="آخر استخدام")
    last_check = Column(DateTime, nullable=True, comment="آخر فحص")
    
    # حالة البروكسي
    is_active = Column(Boolean, default=True, comment="نشط")
    is_working = Column(Boolean, default=True, comment="يعمل")
    status_message = Column(String(500), nullable=True, comment="رسالة الحالة")
    
    # إعدادات
    max_concurrent_requests = Column(Integer, default=5, comment="الحد الأقصى للطلبات المتزامنة")
    timeout = Column(Integer, default=30, comment="مهلة الاتصال بالثواني")
    
    # ملاحظات
    notes = Column(Text, nullable=True, comment="ملاحظات")
    
    # تواريخ النظام
    created_at = Column(DateTime, server_default=func.now(), comment="تاريخ الإنشاء")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="تاريخ التحديث")
    
    def __repr__(self):
        return f"<Proxy(id={self.id}, name='{self.name}', host='{self.host}:{self.port}')>"
    
    def to_dict(self):
        """تحويل إلى قاموس"""
        return {
            "id": self.id,
            "name": self.name,
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "proxy_type": self.proxy_type,
            "country": self.country,
            "city": self.city,
            "ip_address": self.ip_address,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "average_response_time": self.average_response_time,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "is_active": self.is_active,
            "is_working": self.is_working,
            "status_message": self.status_message,
            "max_concurrent_requests": self.max_concurrent_requests,
            "timeout": self.timeout,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @property
    def proxy_url(self):
        """رابط البروكسي الكامل"""
        if self.username and self.password:
            return f"{self.proxy_type}://{self.username}:{self.password}@{self.host}:{self.port}"
        else:
            return f"{self.proxy_type}://{self.host}:{self.port}"
    
    @property
    def success_rate(self):
        """معدل نجاح البروكسي"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    def increment_request_count(self, success: bool = True, response_time: float = 0.0):
        """زيادة عداد الطلبات وتحديث الإحصائيات"""
        from datetime import datetime
        
        self.total_requests += 1
        self.last_used = datetime.utcnow()
        
        if success:
            self.successful_requests += 1
            # تحديث متوسط وقت الاستجابة
            if self.average_response_time == 0:
                self.average_response_time = response_time
            else:
                self.average_response_time = (
                    (self.average_response_time * (self.successful_requests - 1) + response_time) / 
                    self.successful_requests
                )
        else:
            self.failed_requests += 1
    
    def can_handle_request(self):
        """هل يمكن للبروكسي التعامل مع طلب جديد؟"""
        return (self.is_active and 
                self.is_working and 
                self.success_rate >= 70)  # معدل نجاح لا يقل عن 70%