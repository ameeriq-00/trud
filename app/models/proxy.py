"""
نموذج البروكسيات - Proxy Model محسن
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timedelta
from app.core.database import Base


class Proxy(Base):
    __tablename__ = "proxies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="اسم البروكسي")
    
    # معلومات الاتصال
    host = Column(String(255), nullable=False, comment="عنوان الخادم")
    port = Column(Integer, nullable=False, comment="المنفذ")
    username = Column(String(100), nullable=True, comment="اسم المستخدم")
    password = Column(String(255), nullable=True, comment="كلمة المرور")
    proxy_type = Column(String(20), default="http", comment="نوع البروكسي")
    
    # معلومات الموقع
    country = Column(String(50), nullable=True, comment="البلد")
    city = Column(String(100), nullable=True, comment="المدينة")
    
    # إعدادات الأداء
    timeout = Column(Integer, default=30, comment="مهلة الاتصال بالثواني")
    max_concurrent_requests = Column(Integer, default=5, comment="الحد الأقصى للطلبات المتزامنة")
    current_concurrent_requests = Column(Integer, default=0, comment="الطلبات المتزامنة الحالية")
    
    # إحصائيات الاستخدام
    total_requests = Column(Integer, default=0, comment="إجمالي الطلبات")
    successful_requests = Column(Integer, default=0, comment="الطلبات الناجحة")
    failed_requests = Column(Integer, default=0, comment="الطلبات الفاشلة")
    last_used = Column(DateTime, nullable=True, comment="آخر استخدام")
    
    # معلومات الأداء
    average_response_time = Column(Float, default=0.0, comment="متوسط وقت الاستجابة")
    last_response_time = Column(Float, default=0.0, comment="آخر وقت استجابة")
    uptime_percentage = Column(Float, default=100.0, comment="نسبة الوقت النشط")
    
    # حالة البروكسي
    is_active = Column(Boolean, default=True, comment="نشط")
    is_working = Column(Boolean, default=True, comment="يعمل")
    last_check = Column(DateTime, nullable=True, comment="آخر فحص")
    status_message = Column(String(500), nullable=True, comment="رسالة الحالة")
    
    # معلومات إضافية
    notes = Column(Text, nullable=True, comment="ملاحظات")
    
    # تواريخ النظام
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="تاريخ الإنشاء")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="تاريخ التحديث")
    
    # العلاقات
    sessions = relationship("Session", back_populates="proxy")
    
    def __repr__(self):
        return f"<Proxy {self.name}: {self.host}:{self.port}>"
    
    @property
    def success_rate(self) -> float:
        """معدل النجاح"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    @property
    def failure_rate(self) -> float:
        """معدل الفشل"""
        return 100.0 - self.success_rate
    
    @property
    def proxy_url(self) -> str:
        """رابط البروكسي الكامل"""
        if self.username and self.password:
            return f"{self.proxy_type}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.proxy_type}://{self.host}:{self.port}"
    
    @property
    def is_overloaded(self) -> bool:
        """هل البروكسي محمل بشكل مفرط"""
        return self.current_concurrent_requests >= self.max_concurrent_requests
    
    @property
    def health_score(self) -> float:
        """درجة صحة البروكسي (0-100)"""
        if not self.is_working:
            return 0.0
        
        score = 100.0
        
        # خصم نقاط حسب معدل الفشل
        if self.failure_rate > 20:
            score -= 30
        elif self.failure_rate > 10:
            score -= 15
        elif self.failure_rate > 5:
            score -= 5
        
        # خصم نقاط حسب وقت الاستجابة
        if self.average_response_time > 10:
            score -= 20
        elif self.average_response_time > 5:
            score -= 10
        
        # خصم نقاط إذا لم يتم استخدامه مؤخراً
        if self.last_used:
            hours_since_use = (datetime.utcnow() - self.last_used).total_seconds() / 3600
            if hours_since_use > 24:
                score -= 10
        
        return max(0.0, score)
    
    def increment_request_count(self, success: bool, response_time: float = 0.0):
        """زيادة عداد الطلبات"""
        self.total_requests += 1
        self.last_used = datetime.utcnow()
        self.last_response_time = response_time
        
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
        
        # تحديث متوسط وقت الاستجابة
        if self.total_requests == 1:
            self.average_response_time = response_time
        else:
            self.average_response_time = (
                (self.average_response_time * (self.total_requests - 1) + response_time) 
                / self.total_requests
            )
    
    def mark_as_working(self, status_message: str = "Working"):
        """تمييز البروكسي كعامل"""
        self.is_working = True
        self.last_check = datetime.utcnow()
        self.status_message = status_message
    
    def mark_as_not_working(self, error_message: str):
        """تمييز البروكسي كغير عامل"""
        self.is_working = False
        self.last_check = datetime.utcnow()
        self.status_message = error_message
    
    def can_handle_request(self) -> bool:
        """هل يمكن للبروكسي التعامل مع طلب جديد"""
        return (
            self.is_active and 
            self.is_working and 
            not self.is_overloaded
        )
    
    def to_dict(self) -> dict:
        """تحويل إلى قاموس"""
        return {
            "id": self.id,
            "name": self.name,
            "host": self.host,
            "port": self.port,
            "proxy_type": self.proxy_type,
            "country": self.country,
            "city": self.city,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": self.success_rate,
            "average_response_time": self.average_response_time,
            "is_active": self.is_active,
            "is_working": self.is_working,
            "health_score": self.health_score,
            "status_message": self.status_message,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }