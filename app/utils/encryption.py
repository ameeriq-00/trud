"""
وظائف التشفير المحاكي لـ HelloCallers API
بناءً على تحليل ملف HAR - إصدار محسن
"""
import base64
import hashlib
import hmac
import json
import random
import string
import time
import re
import secrets
from typing import Dict, Any, Optional, List
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class HelloCallersEncryption:
    """
    فئة التشفير المحاكي لـ HelloCallers - محسنة بناءً على تحليل HAR
    
    الأنماط المكتشفة:
    1. payload = base64_part + "==" + signature_part
    2. base64_part: عادة 16-24 حرف قبل ==
    3. signature_part: 32-60 حرف، يحتوي على أحرف وأرقام و + / =
    """
    
    def __init__(self, secret_key: str = "hellocallers_secret"):
        self.secret_key = secret_key.encode()
        self.salt = b"hellocallers_salt_2025"
        
        # أنماط الـ payloads الحقيقية من HAR للمرجع
        self.har_examples = [
            "dzhidHJxemZ3N2dpdHBqZg==Lr+iIRK0VVu6JgCLWUMHyuFZNrYQSGG5UcOKjzYp/Kd/g45JWenw8AO8Qw/sAjKi",
            "Y3huYnlzZjlzY3g0ZDYwYg==pToJp06aw5GVetc7RFN4WD+vtr0ICGoRudW90mIeS4k=",
            "NHBodzkyNHI2OHRhczNwZA==Tsd0BJ15wccIY8wKfOjsnw=="
        ]
        
        # تحليل الأنماط
        self.pattern_analysis = self._analyze_har_patterns()
        
        # إنشاء مفتاح التشفير
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.secret_key))
        self.fernet = Fernet(key)
    
    def _analyze_har_patterns(self) -> Dict[str, Any]:
        """تحليل الأنماط من أمثلة HAR الحقيقية"""
        
        analysis = {
            "base64_lengths": [],
            "signature_lengths": [],
            "base64_patterns": [],
            "signature_patterns": []
        }
        
        for payload in self.har_examples:
            if "==" in payload:
                parts = payload.split("==")
                if len(parts) == 2:
                    base64_part, signature_part = parts
                    
                    analysis["base64_lengths"].append(len(base64_part))
                    analysis["signature_lengths"].append(len(signature_part))
                    analysis["base64_patterns"].append(base64_part)
                    analysis["signature_patterns"].append(signature_part)
        
        # حساب المتوسطات
        if analysis["base64_lengths"]:
            analysis["avg_base64_length"] = sum(analysis["base64_lengths"]) // len(analysis["base64_lengths"])
            analysis["avg_signature_length"] = sum(analysis["signature_lengths"]) // len(analysis["signature_lengths"])
        
        return analysis
    
    def _generate_realistic_base64_part(self, data: str, target_length: int = None) -> str:
        """إنشاء الجزء الأول من الـ payload (قبل ==)"""
        
        if target_length is None:
            target_length = random.choice([16, 18, 20, 22, 24])  # أطوال شائعة
        
        # إنشاء بيانات مُركبة
        timestamp = str(int(time.time()))[-8:]  # آخر 8 أرقام من timestamp
        device_hash = hashlib.md5(f"{data}_{timestamp}".encode()).hexdigest()[:8]
        
        # دمج البيانات
        combined = f"{device_hash}{timestamp}"
        
        # تشفير base64
        base64_encoded = base64.b64encode(combined.encode()).decode()
        
        # قطع أو إضافة للوصول للطول المطلوب
        if len(base64_encoded) > target_length:
            return base64_encoded[:target_length]
        elif len(base64_encoded) < target_length:
            # إضافة أحرف عشوائية
            padding_needed = target_length - len(base64_encoded)
            padding = ''.join(random.choices(string.ascii_letters + string.digits, k=padding_needed))
            return base64_encoded + padding
        
        return base64_encoded
    
    def _generate_realistic_signature(self, base64_part: str, data: str) -> str:
        """إنشاء التوقيع (الجزء بعد ==)"""
        
        # أطوال التوقيعات من التحليل
        signature_lengths = [32, 44, 60, 64]  # أطوال شائعة
        target_length = random.choice(signature_lengths)
        
        # إنشاء مفتاح للتوقيع
        secret_key = f"hellocallers_default_2025"
        
        # البيانات للتوقيع
        sign_data = f"{base64_part}_{data}_{int(time.time())}"
        
        # إنشاء HMAC
        signature = hmac.new(
            secret_key.encode(),
            sign_data.encode(),
            hashlib.sha256
        ).digest()
        
        # تحويل لـ base64
        signature_b64 = base64.b64encode(signature).decode()
        
        # تعديل الطول والنمط ليكون مشابهاً للـ HAR
        signature_clean = signature_b64.replace('=', '').replace('+', random.choice(['+', '-'])).replace('/', random.choice(['/', '_']))
        
        if len(signature_clean) > target_length:
            return signature_clean[:target_length]
        elif len(signature_clean) < target_length:
            # إضافة أحرف عشوائية بنمط مشابه
            padding_chars = string.ascii_letters + string.digits + '+/='
            padding = ''.join(random.choices(padding_chars, k=target_length - len(signature_clean)))
            return signature_clean + padding
        
        return signature_clean
    
    def generate_realistic_payload(self, data: str, extra_entropy: bool = True) -> str:
        """
        إنشاء payload مشفر محاكي لـ HelloCallers - محسن
        """
        
        # إضافة عشوائية إضافية للبيانات
        if extra_entropy:
            timestamp = str(int(time.time()))
            random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
            enhanced_data = f"{data}_{timestamp}_{random_suffix}"
        else:
            enhanced_data = data
        
        # إنشاء base64 part
        base64_part = self._generate_realistic_base64_part(enhanced_data)
        
        # إنشاء signature part
        signature_part = self._generate_realistic_signature(base64_part, enhanced_data)
        
        # دمج الأجزاء
        payload = f"{base64_part}=={signature_part}"
        
        return payload
    
    def encrypt_phone_search(self, phone_number: str) -> str:
        """تشفير رقم الهاتف للبحث"""
        
        # تنظيف رقم الهاتف
        cleaned_phone = re.sub(r'[^0-9]', '', phone_number)
        
        # إنشاء base64 part
        base64_part = self._generate_realistic_base64_part(cleaned_phone)
        
        # إنشاء signature part
        signature_part = self._generate_realistic_signature(base64_part, cleaned_phone)
        
        # دمج الأجزاء
        payload = f"{base64_part}=={signature_part}"
        
        return payload
    
    def encrypt_history_request(self, user_id: Optional[str] = None) -> str:
        """تشفير طلب التاريخ"""
        
        history_data = f"history_request_{user_id or 'anonymous'}_{int(time.time())}"
        
        base64_part = self._generate_realistic_base64_part(history_data, target_length=22)
        signature_part = self._generate_realistic_signature(base64_part, history_data)
        
        return f"{base64_part}=={signature_part}"
    
    def encrypt_user_info_request(self) -> str:
        """تشفير طلب معلومات المستخدم"""
        
        user_info_data = f"user_info_{int(time.time())}"
        
        base64_part = self._generate_realistic_base64_part(user_info_data, target_length=20)
        signature_part = self._generate_realistic_signature(base64_part, user_info_data)
        
        return f"{base64_part}=={signature_part}"
    
    def create_encrypted_form_data(self, data: str) -> Dict[str, str]:
        """إنشاء form data مشفر للـ POST requests"""
        
        encrypted_payload = self.generate_realistic_payload(data)
        
        return {
            "payload": encrypted_payload
        }
    
    def validate_payload_format(self, payload: str) -> bool:
        """التحقق من صحة تنسيق الـ payload"""
        
        if "==" not in payload:
            return False
        
        parts = payload.split("==")
        if len(parts) != 2:
            return False
        
        base64_part, signature_part = parts
        
        # فحص طول الأجزاء
        if not (10 <= len(base64_part) <= 30):
            return False
        
        if not (20 <= len(signature_part) <= 70):
            return False
        
        # فحص أن base64_part يحتوي على أحرف صحيحة
        if not re.match(r'^[A-Za-z0-9+/]*$', base64_part):
            return False
        
        return True
    
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
    
    def debug_payload_analysis(self, payload: str) -> Dict[str, Any]:
        """تحليل الـ payload لأغراض التصحيح"""
        
        analysis = {
            "original_payload": payload,
            "is_valid_format": self.validate_payload_format(payload),
            "total_length": len(payload),
            "has_double_equals": "==" in payload
        }
        
        if "==" in payload:
            parts = payload.split("==")
            if len(parts) == 2:
                base64_part, signature_part = parts
                
                analysis.update({
                    "base64_part": base64_part,
                    "base64_length": len(base64_part),
                    "signature_part": signature_part,
                    "signature_length": len(signature_part),
                    "matches_har_pattern": self._matches_har_pattern(base64_part, signature_part)
                })
        
        return analysis
    
    def _matches_har_pattern(self, base64_part: str, signature_part: str) -> bool:
        """فحص مطابقة النمط مع أمثلة HAR"""
        
        # فحص أطوال مشابهة
        base64_in_range = 15 <= len(base64_part) <= 25
        signature_in_range = 30 <= len(signature_part) <= 65
        
        # فحص أحرف صحيحة
        valid_base64_chars = re.match(r'^[A-Za-z0-9+/]*$', base64_part)
        valid_signature_chars = re.match(r'^[A-Za-z0-9+/=_-]*$', signature_part)
        
        return all([base64_in_range, signature_in_range, valid_base64_chars, valid_signature_chars])
    
    def _generate_device_id(self) -> str:
        """إنشاء device ID مشابه للأنماط الحقيقية"""
        return ''.join(random.choices('abcdef0123456789', k=16))
    
    def _generate_player_id(self) -> str:
        """إنشاء player ID مشابه للأنماط الحقيقية"""
        return f"{secrets.token_hex(4)}-{secrets.token_hex(2)}-{secrets.token_hex(2)}-{secrets.token_hex(2)}-{secrets.token_hex(6)}"
    
    def get_realistic_headers(self, account_data: Dict[str, Any], endpoint: str = "search") -> Dict[str, str]:
        """إنشاء headers واقعية بناءً على تحليل HAR"""
        
        # User agents واقعية من تحليل HAR
        user_agents = [
            "okhttp/5.0.0-alpha.2",
            "okhttp/4.12.0",
            "okhttp/4.11.0",
            "okhttp/5.0.0",
            "Dalvik/2.1.0 (Linux; U; Android 11; SM-A505F Build/RP1A.200720.012)",
            "Dalvik/2.1.0 (Linux; U; Android 12; SM-G973F Build/SP1A.210812.016)"
        ]
        
        headers = {
            "authorization": f"Bearer {account_data.get('token', '')}",
            "api-version": "1",
            "x-request-encrypted": "1",
            "accept": "application/json",
            "device-type": "android",
            "android-app": "main",
            "locale": account_data.get("locale", "ar"),
            "player-id": account_data.get("player_id", self._generate_player_id()),
            "device-id": account_data.get("device_id", self._generate_device_id()),
            "country": account_data.get("country", "IQ"),
            "host": "hellocallers.com",
            "connection": "Keep-Alive",
            "accept-encoding": "gzip",
            "user-agent": random.choice(user_agents)
        }
        
        # headers خاصة حسب نوع الطلب
        if endpoint in ["search", "histories"]:
            headers["content-type"] = "application/x-www-form-urlencoded"
        elif endpoint == "user_info":
            headers["content-type"] = "application/json"
        
        return headers


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
    
    def create_bulk_payloads(self, phone_numbers: List[str]) -> List[Dict[str, str]]:
        """إنشاء عدة payloads للبحث المجمع"""
        
        payloads = []
        
        for phone in phone_numbers:
            payload = self.encrypt_phone_search(phone)
            
            payloads.append({
                "phone_number": phone,
                "payload": payload,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # تأخير صغير لتجنب التكرار في timestamps
            time.sleep(0.001)
        
        return payloads


# الثوابت المستخرجة من HAR
HAR_PAYLOAD_EXAMPLES = [
    "Y3huYnlzZjlzY3g0ZDYwYg==pToJp06aw5GVetc7RFN4WD+vtr0ICGoRudW90mIeS4k=",
    "NHBodzkyNHI2OHRhczNwZA==Tsd0BJ15wccIY8wKfOjsnw==",
    "dzhidHJxemZ3N2dpdHBqZg==Lr+iIRK0VVu6JgCLWUMHyuFZNrYQSGG5UcOKjzYp/Kd/g45JWenw8AO8Qw/sAjKi"
]


def get_har_example_payload() -> str:
    """الحصول على payload مثال من HAR"""
    return random.choice(HAR_PAYLOAD_EXAMPLES)


def create_realistic_payload(data: str) -> str:
    """إنشاء payload محاكي - دالة مساعدة"""
    encryptor = HelloCallersEncryption()
    return encryptor.generate_realistic_payload(data)


def create_phone_search_payload(phone_number: str) -> str:
    """إنشاء payload للبحث عن رقم - دالة مساعدة"""
    encryptor = HelloCallersEncryption()
    return encryptor.encrypt_phone_search(phone_number)


def generate_request_variations(phone: str, count: int = 5) -> List[str]:
    """إنشاء عدة اختلافات لنفس الطلب"""
    encryptor = EnhancedEncryption()
    return [encryptor.encrypt_phone_search(phone) for _ in range(count)]