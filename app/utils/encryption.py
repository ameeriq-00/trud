"""
وظائف التشفير المحاكي لـ HelloCallers API
بناءً على تحليل ملف HAR
"""
import base64
import hashlib
import hmac
import json
import random
import string
import time
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class HelloCallersEncryption:
    """
    فئة التشفير المحاكي لـ HelloCallers
    
    بناءً على تحليل HAR، يستخدم HelloCallers نظام تشفير مخصص:
    payload = base64_encoded_data + "==" + signature
    """
    
    def __init__(self, secret_key: str = "hellocallers_secret"):
        self.secret_key = secret_key.encode()
        self.salt = b"hellocallers_salt_2025"
        
        # إنشاء مفتاح التشفير
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.secret_key))
        self.fernet = Fernet(key)
    
    def generate_realistic_payload(self, data: str, extra_entropy: bool = True) -> str:
        """
        إنشاء payload مشفر محاكي لـ HelloCallers
        
        النمط المكتشف من HAR:
        payload = base64_data + "==" + signature
        """
        
        # إضافة عشوائية إضافية للبيانات
        if extra_entropy:
            timestamp = str(int(time.time()))
            random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
            enhanced_data = f"{data}_{timestamp}_{random_suffix}"
        else:
            enhanced_data = data
        
        # تشفير البيانات
        base64_data = base64.b64encode(enhanced_data.encode()).decode()
        
        # إنشاء التوقيع المحاكي
        signature = self._generate_signature(base64_data)
        
        # دمج البيانات بالنمط المكتشف
        payload = f"{base64_data}=={signature}"
        
        return payload
    
    def _generate_signature(self, data: str) -> str:
        """إنشاء توقيع محاكي للبيانات"""
        
        # استخدام HMAC-SHA256 لإنشاء توقيع
        message = f"{data}{int(time.time())}"
        signature = hmac.new(
            self.secret_key,
            message.encode(),
            hashlib.sha256
        ).digest()
        
        # تحويل إلى base64 مع تعديلات محاكية
        b64_signature = base64.b64encode(signature).decode()
        
        # محاكاة نمط التوقيع من HAR
        # إزالة بعض الحروف وإضافة أخرى لمحاكاة النمط
        modified_signature = self._modify_signature_pattern(b64_signature)
        
        return modified_signature
    
    def _modify_signature_pattern(self, signature: str) -> str:
        """تعديل نمط التوقيع لمحاكاة HelloCallers"""
        
        # إزالة padding
        signature = signature.rstrip('=')
        
        # قطع إلى الطول المناسب (40-44 حرف)
        if len(signature) > 44:
            signature = signature[:44]
        elif len(signature) < 40:
            # إضافة أحرف عشوائية
            padding = ''.join(random.choices(string.ascii_letters + string.digits + '+/', k=40-len(signature)))
            signature += padding
        
        return signature
    
    def encrypt_phone_search(self, phone_number: str) -> str:
        """تشفير رقم الهاتف للبحث"""
        
        # تنظيف رقم الهاتف
        cleaned_phone = phone_number.replace('+', '').replace(' ', '').replace('-', '')
        
        # إنشاء payload للبحث
        search_data = cleaned_phone
        
        return self.generate_realistic_payload(combined_data)
    
    def analyze_har_pattern(self, har_payload: str) -> Dict[str, Any]:
        """
        تحليل نمط التشفير من ملف HAR
        لاستخراج معلومات مفيدة
        """
        
        analysis = {
            "total_length": len(har_payload),
            "has_double_equals": "==" in har_payload,
            "base64_part": "",
            "signature_part": "",
            "pattern_detected": False
        }
        
        if "==" in har_payload:
            parts = har_payload.split("==")
            if len(parts) == 2:
                analysis["base64_part"] = parts[0]
                analysis["signature_part"] = parts[1]
                analysis["pattern_detected"] = True
                analysis["base64_length"] = len(parts[0])
                analysis["signature_length"] = len(parts[1])
        
        return analysis
    
    def generate_har_like_payload(self, data: str) -> str:
        """
        إنشاء payload مشابه تماماً لما في ملف HAR
        """
        
        # الأمثلة من HAR:
        # Y3huYnlzZjlzY3g0ZDYwYg==pToJp06aw5GVetc7RFN4WD+vtr0ICGoRudW90mIeS4k=
        # NHBodzkyNHI2OHRhczNwZA==Tsd0BJ15wccIY8wKfOjsnw==
        
        # تشفير البيانات لـ base64
        base64_data = base64.b64encode(data.encode()).decode().rstrip('=')
        
        # إنشاء توقيع بطول مشابه (32-44 حرف)
        signature_base = hashlib.sha256(f"{data}{time.time()}".encode()).digest()
        signature = base64.b64encode(signature_base).decode().rstrip('=')
        
        # تعديل الطول ليكون مشابه للـ HAR
        if len(signature) > 44:
            signature = signature[:44]
        elif len(signature) < 32:
            signature = signature + ''.join(random.choices(string.ascii_letters + string.digits, k=32-len(signature)))
        
        return f"{base64_data}=={signature}"


class EnhancedEncryption(HelloCallersEncryption):
    """
    فئة التشفير المحسنة مع ميزات إضافية
    """
    
    def __init__(self, secret_key: str = "hellocallers_secret"):
        super().__init__(secret_key)
        self.request_counter = 0
        self.session_id = self._generate_session_id()
    
    def _generate_session_id(self) -> str:
        """إنشاء معرف جلسة فريد"""
        return hashlib.md5(f"session_{time.time()}_{random.randint(1000, 9999)}".encode()).hexdigest()[:16]
    
    def encrypt_with_session(self, data: str, include_counter: bool = True) -> str:
        """تشفير مع معلومات الجلسة"""
        
        if include_counter:
            self.request_counter += 1
            session_data = f"{data}_{self.session_id}_{self.request_counter}"
        else:
            session_data = f"{data}_{self.session_id}"
        
        return self.generate_realistic_payload(session_data)
    
    def create_anti_detection_payload(self, phone_number: str, user_agent: str) -> str:
        """
        إنشاء payload مقاوم للكشف
        """
        
        # إنشاء بصمة مبنية على user agent
        ua_hash = hashlib.md5(user_agent.encode()).hexdigest()[:8]
        
        # إضافة تشويش
        noise = ''.join(random.choices(string.ascii_lowercase, k=6))
        
        # دمج البيانات
        anti_detect_data = f"{phone_number}_{ua_hash}_{noise}_{int(time.time() * 1000) % 100000}"
        
        return self.generate_realistic_payload(anti_detect_data)
    
    def rotate_encryption_method(self, data: str, method: str = "auto") -> str:
        """
        تدوير طريقة التشفير لتجنب الكشف
        """
        
        methods = ["basic", "enhanced", "session", "anti_detect"]
        
        if method == "auto":
            method = random.choice(methods)
        
        if method == "basic":
            return self.generate_realistic_payload(data, extra_entropy=False)
        elif method == "enhanced":
            return self.generate_realistic_payload(data, extra_entropy=True)
        elif method == "session":
            return self.encrypt_with_session(data)
        elif method == "anti_detect":
            return self.create_anti_detection_payload(data, "okhttp/5.0.0-alpha.2")
        else:
            return self.generate_realistic_payload(data)


# دوال مساعدة عامة للتشفير

def quick_encrypt_phone(phone: str) -> str:
    """تشفير سريع لرقم الهاتف"""
    encryptor = HelloCallersEncryption()
    return encryptor.encrypt_phone_search(phone)


def create_form_payload(data: str) -> Dict[str, str]:
    """إنشاء form payload سريع"""
    encryptor = HelloCallersEncryption()
    return encryptor.create_encrypted_form_data(data)


def simulate_mobile_encryption(phone: str, device_info: Dict[str, str]) -> str:
    """محاكاة تشفير الهاتف المحمول"""
    encryptor = HelloCallersEncryption()
    return encryptor.simulate_android_encryption(phone, device_info)


def analyze_har_encryption(har_payload: str) -> Dict[str, Any]:
    """تحليل تشفير من ملف HAR"""
    encryptor = HelloCallersEncryption()
    return encryptor.analyze_har_pattern(har_payload)


def generate_realistic_variations(phone: str, count: int = 5) -> list[str]:
    """إنشاء تنويعات واقعية للطلب"""
    encryptor = EnhancedEncryption()
    return encryptor.generate_request_variations(phone, count)


# الثوابت المستخرجة من HAR
HAR_PAYLOAD_EXAMPLES = [
    "Y3huYnlzZjlzY3g0ZDYwYg==pToJp06aw5GVetc7RFN4WD+vtr0ICGoRudW90mIeS4k=",
    "NHBodzkyNHI2OHRhczNwZA==Tsd0BJ15wccIY8wKfOjsnw==",
    "dzhidHJxemZ3N2dpdHBqZg==Lr+iIRK0VVu6JgCLWUMHyuFZNrYQSGG5UcOKjzYp/Kd/g45JWenw8AO8Qw/sAjKi"
]

def get_har_example_payload() -> str:
    """الحصول على payload مثال من HAR"""
    return random.choice(HAR_PAYLOAD_EXAMPLES)


def validate_payload_format(payload: str) -> bool:
    """التحقق من صيغة الـ payload"""
    
    # يجب أن يحتوي على ==
    if "==" not in payload:
        return False
    
    parts = payload.split("==")
    if len(parts) != 2:
        return False
    
    base64_part, signature_part = parts
    
    # فحص base64
    try:
        base64.b64decode(base64_part + "==")  # إضافة padding
    except:
        return False
    
    # فحص طول التوقيع
    if len(signature_part) < 20 or len(signature_part) > 60:
        return False
    
    return Truepayload(search_data)
    
def encrypt_history_request(self, user_id: Optional[str] = None) -> str:
    """تشفير طلب التاريخ"""
    
    # بيانات طلب التاريخ
    history_data = f"history_request_{user_id or 'anonymous'}_{int(time.time())}"
    
    return self.generate_realistic_payload(history_data, extra_entropy=False)

def encrypt_user_info_request(self) -> str:
    """تشفير طلب معلومات المستخدم"""
    
    user_info_data = f"user_info_{int(time.time())}"
    
    return self.generate_realistic_payload(user_info_data, extra_entropy=False)

def create_encrypted_form_data(self, data: str) -> Dict[str, str]:
    """إنشاء form data مشفر للـ POST requests"""
    
    encrypted_payload = self.generate_realistic_payload(data)
    
    return {
        "payload": encrypted_payload
    }

def simulate_android_encryption(self, phone_number: str, device_info: Dict[str, str]) -> str:
    """
    محاكاة التشفير من تطبيق الأندرويد
    بناءً على device fingerprint
    """
    
    # دمج معلومات الجهاز مع رقم الهاتف
    device_signature = f"{device_info.get('device_id', '')}_{device_info.get('player_id', '')}"
    combined_data = f"{phone_number}_{device_signature}"
    
    # إنشاء hash مخصص للجهاز
    device_hash = hashlib.md5(device_signature.encode()).hexdigest()[:16]
    
    # تشفير مع بصمة الجهاز
    enhanced_data = f"{combined_data}_{device_hash}"
    
    return self.generate_realistic_payload(enhanced_data)

def validate_response_signature(self, response_data: str, signature: str) -> bool:
    """التحقق من توقيع الاستجابة (محاكي)"""
    
    # محاكاة التحقق من التوقيع
    expected_signature = self._generate_signature(response_data)
    
    # مقارنة مرنة (محاكية)
    return len(signature) >= 40 and len(expected_signature) >= 40

def decrypt_response(self, encrypted_response: str) -> Optional[Dict[str, Any]]:
    """فك تشفير الاستجابة (محاكي)"""
    
    try:
        # في الواقع، HelloCallers يرسل JSON غير مشفر
        # هذه الدالة للمحاكاة المستقبلية فقط
        
        if encrypted_response.startswith('{'):
            # JSON عادي
            return json.loads(encrypted_response)
        
        # محاولة فك base64
        try:
            decoded = base64.b64decode(encrypted_response)
            return json.loads(decoded.decode())
        except:
            return None
            
    except Exception:
        return None

def generate_request_variations(self, phone_number: str, count: int = 3) -> list[str]:
    """
    إنشاء عدة أشكال مختلفة من نفس الطلب
    للتنويع وتجنب الكشف
    """
    
    variations = []
    
    for i in range(count):
        # تنويع في البيانات الإضافية
        variation_data = f"{phone_number}_variation_{i}_{random.randint(1000, 9999)}"
        
        # تأخير صغير لضمان timestamps مختلفة
        time.sleep(0.01)
        
        encrypted = self.generate_realistic_payload(variation_data)
        variations.append(encrypted)
    
    return variations

def create_batch_payload(self, phone_numbers: list[str]) -> str:
    """إنشاء payload للبحث المجمع"""
    
    # دمج الأرقام في نص واحد
    phones_data = ','.join(phone_numbers)
    batch_identifier = f"batch_{len(phone_numbers)}_{int(time.time())}"
    
    combined_data = f"{phones_data}_{batch_identifier}"
    
    return self.generate_realistic_