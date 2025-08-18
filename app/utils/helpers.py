"""
وظائف مساعدة عامة
"""
import re
import uuid
import hashlib
import random
import string
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import phonenumbers
from phonenumbers import PhoneNumberFormat


def generate_session_id() -> str:
    """إنشاء معرف جلسة فريد"""
    return f"trud_{uuid.uuid4().hex[:16]}"


def generate_device_id() -> str:
    """إنشاء device ID محاكي لأندرويد"""
    # محاكاة Android device ID (16 hex characters)
    return ''.join(random.choices('0123456789abcdef', k=16))


def generate_player_id() -> str:
    """إنشاء player ID محاكي"""
    return str(uuid.uuid4())


def normalize_phone_number(phone: str, default_country: str = "IQ") -> Dict[str, str]:
    """
    تطبيع رقم الهاتف إلى جميع الصيغ المطلوبة
    """
    try:
        # إزالة المسافات والرموز غير المرغوبة
        cleaned_phone = re.sub(r'[^\d+]', '', phone)
        
        # محاولة تحليل الرقم
        parsed = phonenumbers.parse(cleaned_phone, default_country)
        
        if not phonenumbers.is_valid_number(parsed):
            raise ValueError(f"Invalid phone number: {phone}")
        
        return {
            "national": phonenumbers.format_number(parsed, PhoneNumberFormat.NATIONAL),
            "international": phonenumbers.format_number(parsed, PhoneNumberFormat.INTERNATIONAL),
            "e164": phonenumbers.format_number(parsed, PhoneNumberFormat.E164),
            "country_code": str(parsed.country_code),
            "region": phonenumbers.region_code_for_number(parsed)
        }
    
    except Exception as e:
        # fallback للأرقام العراقية
        if phone.startswith('+964'):
            clean_number = phone.replace('+964', '').strip()
            return {
                "national": f"0{clean_number}",
                "international": f"+964 {clean_number}",
                "e164": f"+964{clean_number}",
                "country_code": "964",
                "region": "IQ"
            }
        
        raise ValueError(f"Could not normalize phone number: {phone}")


def validate_phone_number(phone: str) -> bool:
    """التحقق من صحة رقم الهاتف"""
    try:
        normalize_phone_number(phone)
        return True
    except:
        return False


def clean_phone_numbers_list(phone_numbers: List[str]) -> List[str]:
    """تنظيف قائمة أرقام الهواتف وإزالة المكررات"""
    cleaned = []
    seen = set()
    
    for phone in phone_numbers:
        try:
            normalized = normalize_phone_number(phone)
            e164 = normalized["e164"]
            
            if e164 not in seen:
                seen.add(e164)
                cleaned.append(e164)
        except:
            continue  # تخطي الأرقام غير الصالحة
    
    return cleaned


def generate_random_string(length: int = 16) -> str:
    """إنشاء نص عشوائي"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def generate_android_fingerprint() -> Dict[str, str]:
    """إنشاء بصمة أندرويد واقعية"""
    
    android_versions = ["11", "12", "13", "14"]
    devices = [
        "SM-A505F", "SM-G973F", "SM-N975F", "SM-A315F", 
        "Redmi Note 10", "Redmi Note 11", "POCO X3 Pro",
        "OnePlus 8T", "OnePlus 9", "Pixel 6", "Pixel 7"
    ]
    
    android_version = random.choice(android_versions)
    device = random.choice(devices)
    
    return {
        "device_id": generate_device_id(),
        "player_id": generate_player_id(),
        "user_agent": f"okhttp/{random.choice(['5.0.0-alpha.2', '4.12.0', '5.0.0'])}",
        "android_version": android_version,
        "device_model": device,
        "build_version": f"RP1A.200720.{random.randint(10, 99)}"
    }


def calculate_success_rate(successful: int, total: int) -> float:
    """حساب معدل النجاح"""
    if total == 0:
        return 0.0
    return (successful / total) * 100


def format_response_time(seconds: float) -> str:
    """تنسيق وقت الاستجابة"""
    if seconds < 1:
        return f"{int(seconds * 1000)}ms"
    return f"{seconds:.2f}s"


def format_file_size(bytes_size: int) -> str:
    """تنسيق حجم الملف"""
    if bytes_size < 1024:
        return f"{bytes_size}B"
    elif bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.1f}KB"
    else:
        return f"{bytes_size / (1024 * 1024):.1f}MB"


def mask_sensitive_data(data: str, mask_char: str = "*", visible_chars: int = 4) -> str:
    """إخفاء البيانات الحساسة"""
    if len(data) <= visible_chars:
        return mask_char * len(data)
    
    visible_start = data[:visible_chars//2]
    visible_end = data[-visible_chars//2:] if visible_chars//2 > 0 else ""
    masked_middle = mask_char * (len(data) - visible_chars)
    
    return visible_start + masked_middle + visible_end


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """تحليل JSON آمن"""
    try:
        return json.loads(json_str)
    except:
        return default


def safe_json_dumps(obj: Any, default: str = "{}") -> str:
    """تحويل إلى JSON آمن"""
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except:
        return default


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """تقسيم قائمة إلى مجموعات"""
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


def get_random_delay(min_seconds: float = 0.5, max_seconds: float = 3.0) -> float:
    """الحصول على تأخير عشوائي"""
    return random.uniform(min_seconds, max_seconds)


def generate_request_id() -> str:
    """إنشاء معرف طلب فريد"""
    timestamp = int(datetime.now().timestamp() * 1000)
    random_part = random.randint(1000, 9999)
    return f"req_{timestamp}_{random_part}"


def is_spam_indicator(phone_data: Dict) -> bool:
    """
    تحديد ما إذا كان الرقم مؤشر على أنه مزعج
    بناءً على بيانات الاستجابة
    """
    if not phone_data:
        return False
    
    # فحص المؤشرات المباشرة
    if phone_data.get("is_spam"):
        return True
    
    if phone_data.get("spams_count", 0) > 3:
        return True
    
    # فحص الأسماء المشبوهة
    names = phone_data.get("names", [])
    spam_keywords = [
        "spam", "تسويق", "إعلان", "دعاية", "مبيعات", 
        "عروض", "تجاري", "شركة", "مركز اتصال"
    ]
    
    for name_obj in names:
        name = name_obj.get("name", "").lower()
        if any(keyword in name for keyword in spam_keywords):
            return True
    
    return False


def extract_carrier_info(phone_data: Dict) -> Dict[str, str]:
    """استخراج معلومات المشغل من بيانات الرقم"""
    carrier_info = {
        "name": "غير معروف",
        "type": "غير معروف",
        "country": "غير معروف"
    }
    
    if not phone_data:
        return carrier_info
    
    # استخراج اسم المشغل
    carrier_info["name"] = phone_data.get("carrier_name", "غير معروف")
    
    # استخراج نوع المشغل
    carrier_info["type"] = phone_data.get("carrier_type_text", "غير معروف")
    
    # استخراج البلد
    carrier_info["country"] = phone_data.get("country_name", "غير معروف")
    
    return carrier_info


def get_time_periods() -> Dict[str, datetime]:
    """الحصول على فترات زمنية مختلفة"""
    now = datetime.utcnow()
    
    return {
        "last_hour": now - timedelta(hours=1),
        "last_24_hours": now - timedelta(days=1),
        "last_week": now - timedelta(days=7),
        "last_month": now - timedelta(days=30),
        "last_3_months": now - timedelta(days=90)
    }


def calculate_rate_limit_reset(limit_per_hour: int, used_requests: int) -> datetime:
    """حساب وقت إعادة تعيين حد الطلبات"""
    if used_requests < limit_per_hour:
        return datetime.utcnow()
    
    # إعادة التعيين كل ساعة
    now = datetime.utcnow()
    next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    return next_hour


def hash_phone_number(phone: str, salt: str = "trud_salt") -> str:
    """تشفير رقم الهاتف للخصوصية"""
    combined = f"{phone}_{salt}"
    return hashlib.sha256(combined.encode()).hexdigest()[:16]


def validate_bulk_request(phone_numbers: List[str], max_bulk_size: int = 100) -> Dict[str, Any]:
    """التحقق من صحة طلب البحث المجمع"""
    result = {
        "valid": True,
        "errors": [],
        "cleaned_numbers": [],
        "stats": {
            "total_submitted": len(phone_numbers),
            "valid_numbers": 0,
            "invalid_numbers": 0,
            "duplicates_removed": 0
        }
    }
    
    # فحص الحد الأقصى
    if len(phone_numbers) > max_bulk_size:
        result["valid"] = False
        result["errors"].append(f"تم تجاوز الحد الأقصى للأرقام ({max_bulk_size})")
        return result
    
    # تنظيف الأرقام
    cleaned = clean_phone_numbers_list(phone_numbers)
    
    result["cleaned_numbers"] = cleaned
    result["stats"]["valid_numbers"] = len(cleaned)
    result["stats"]["invalid_numbers"] = len(phone_numbers) - len(cleaned)
    result["stats"]["duplicates_removed"] = len(phone_numbers) - len(set(phone_numbers))
    
    if not cleaned:
        result["valid"] = False
        result["errors"].append("لا توجد أرقام صالحة في القائمة")
    
    return result