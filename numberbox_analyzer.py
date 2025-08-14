"""
تحليل NumberBox - إصلاح خطأ entropy
"""
import base64
import json
import hashlib
import hmac
from typing import Dict, Tuple, Optional
import binascii
import struct
import zlib
import math

class NumberBoxDecryptor:
    def __init__(self):
        # البيانات الأساسية للتحليل
        self.phone = "+9647809394930"
        self.ccode_encrypted = "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"  # الـ ccode الكامل
        self.number_encrypted = "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"  # الـ number الكامل
        
        # إعدادات التطبيق المستخرجة من HAR
        self.device_info = {
            "device": "android",
            "model": "SM-A505F",
            "android_api": 30,
            "user_agent": "okhttp/4.12.0",
            "version": "7.7.3"
        }
    
    def calculate_entropy(self, data: bytes) -> float:
        """حساب entropy للبيانات - مُصحح"""
        if not data:
            return 0
        
        byte_counts = [0] * 256
        for byte in data:
            byte_counts[byte] += 1
        
        entropy = 0
        data_len = len(data)
        for count in byte_counts:
            if count > 0:
                p = count / data_len
                entropy -= p * math.log2(p)  # استخدام math.log2 بدلاً من bit_length
        
        return entropy
    
    def analyze_base64_structure(self, encrypted_data: str) -> Dict:
        """تحليل بنية البيانات المشفرة"""
        try:
            # فك base64
            decoded = base64.b64decode(encrypted_data)
            
            return {
                "original_length": len(encrypted_data),
                "decoded_length": len(decoded),
                "hex_data": decoded.hex()[:100],  # أول 100 حرف فقط
                "first_bytes": decoded[:16].hex(),
                "last_bytes": decoded[-16:].hex(),
                "entropy": round(self.calculate_entropy(decoded), 2),
                "possible_compression": self.check_compression_headers(decoded)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def check_compression_headers(self, data: bytes) -> Dict:
        """فحص headers الضغط الشائعة"""
        headers = {
            "gzip": data.startswith(b'\x1f\x8b'),
            "zlib": data.startswith(b'\x78'),
            "bzip2": data.startswith(b'BZ'),
            "lzma": data.startswith(b'\xfd7zXZ'),
        }
        
        # محاولة فك ضغط zlib
        try:
            decompressed = zlib.decompress(data)
            headers["zlib_success"] = True
            headers["decompressed_preview"] = decompressed[:50].hex()
            headers["decompressed_size"] = len(decompressed)
        except:
            headers["zlib_success"] = False
            
        return headers
    
    def analyze_number_structure(self) -> Dict:
        """تحليل متقدم لبنية number المشفر"""
        try:
            decoded = base64.b64decode(self.number_encrypted)
            
            analysis = {
                "size_analysis": {
                    "total_bytes": len(decoded),
                    "unique_bytes": len(set(decoded)),
                    "entropy": round(self.calculate_entropy(decoded), 2)
                },
                "potential_structures": self.identify_potential_structures(decoded),
                "phone_search": self.search_phone_in_data(decoded),
                "statistical_analysis": self.statistical_analysis(decoded)
            }
            
            return analysis
            
        except Exception as e:
            return {"error": str(e)}
    
    def identify_potential_structures(self, data: bytes) -> Dict:
        """تحديد البنى المحتملة للبيانات"""
        structures = {}
        
        # فحص إذا كانت البيانات JSON مشفرة
        try:
            # محاولة تفسير البيانات كـ JSON بعد فك تشفير بسيط
            text_attempts = [
                data.decode('utf-8', errors='ignore'),
                data.decode('latin-1', errors='ignore'),
            ]
            
            for attempt in text_attempts:
                if '{' in attempt and '}' in attempt:
                    structures["possible_json"] = True
                    structures["json_preview"] = attempt[:100]
                    break
        except:
            pass
        
        # فحص أنماط رقم الهاتف
        phone_patterns = [
            self.phone.encode(),
            self.phone[1:].encode(),  # بدون +
            self.phone.replace("+964", "0").encode(),
            str(int(self.phone[1:])).encode()  # كرقم صحيح
        ]
        
        for i, pattern in enumerate(phone_patterns):
            if pattern in data:
                structures[f"phone_pattern_{i}"] = {
                    "pattern": pattern.decode(),
                    "found": True,
                    "position": data.find(pattern)
                }
        
        return structures
    
    def search_phone_in_data(self, data: bytes) -> Dict:
        """البحث المتقدم عن رقم الهاتف في البيانات"""
        
        phone_searches = {
            "exact_match": self.phone.encode() in data,
            "without_plus": self.phone[1:].encode() in data,
            "local_format": self.phone.replace("+964", "0").encode() in data,
            "digits_only": "".join(filter(str.isdigit, self.phone)).encode() in data
        }
        
        # البحث عن أجزاء من الرقم
        phone_digits = "".join(filter(str.isdigit, self.phone))
        chunks = [phone_digits[i:i+4] for i in range(0, len(phone_digits), 4)]
        
        chunk_matches = {}
        for i, chunk in enumerate(chunks):
            chunk_matches[f"chunk_{i}"] = chunk.encode() in data
        
        return {
            "format_matches": phone_searches,
            "chunk_matches": chunk_matches,
            "phone_digits": phone_digits
        }
    
    def statistical_analysis(self, data: bytes) -> Dict:
        """تحليل إحصائي متقدم"""
        
        # تحليل التوزيع
        byte_freq = {}
        for byte in data:
            byte_freq[byte] = byte_freq.get(byte, 0) + 1
        
        # حساب إحصائيات
        frequencies = list(byte_freq.values())
        
        stats = {
            "mean_frequency": sum(frequencies) / len(frequencies),
            "max_frequency": max(frequencies),
            "min_frequency": min(frequencies),
            "std_deviation": self.calculate_std_dev(frequencies)
        }
        
        # تحليل الأنماط المتتالية
        patterns = self.analyze_sequential_patterns(data)
        
        return {
            "frequency_stats": stats,
            "sequential_patterns": patterns,
            "randomness_indicators": self.assess_randomness(data)
        }
    
    def calculate_std_dev(self, values: list) -> float:
        """حساب الانحراف المعياري"""
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return math.sqrt(variance)
    
    def analyze_sequential_patterns(self, data: bytes) -> Dict:
        """تحليل الأنماط المتتالية"""
        
        # البحث عن تكرارات
        repeats = {}
        for length in [2, 3, 4]:
            for i in range(len(data) - length):
                pattern = data[i:i+length]
                count = sum(1 for j in range(i+1, len(data)-length) 
                           if data[j:j+length] == pattern)
                if count > 0:
                    key = f"pattern_{length}_{pattern.hex()}"
                    repeats[key] = count
        
        return {
            "repeated_sequences": dict(list(repeats.items())[:5]),  # أول 5
            "total_patterns": len(repeats)
        }
    
    def assess_randomness(self, data: bytes) -> Dict:
        """تقييم مستوى العشوائية"""
        
        # اختبار runs (تتابع نفس القيمة)
        runs = 0
        current_run = 1
        
        for i in range(1, len(data)):
            if data[i] == data[i-1]:
                current_run += 1
            else:
                runs += 1
                current_run = 1
        
        # تحليل التوزيع
        entropy = self.calculate_entropy(data)
        max_entropy = 8.0  # أقصى entropy لبايت واحد
        
        return {
            "entropy_ratio": round(entropy / max_entropy, 3),
            "runs_count": runs,
            "avg_run_length": round(len(data) / runs, 2) if runs > 0 else 0,
            "randomness_assessment": self.classify_randomness(entropy)
        }
    
    def classify_randomness(self, entropy: float) -> str:
        """تصنيف مستوى العشوائية"""
        if entropy > 7.5:
            return "High (likely encrypted)"
        elif entropy > 6.5:
            return "Medium (possibly compressed/encoded)"
        elif entropy > 4.0:
            return "Low (likely plaintext with encoding)"
        else:
            return "Very low (possibly structured data)"
    
    def attempt_simple_decryption_methods(self) -> Dict:
        """محاولة طرق فك تشفير بسيطة"""
        
        try:
            decoded = base64.b64decode(self.number_encrypted)
            results = {}
            
            # محاولة 1: XOR مع مفاتيح مختلفة
            xor_keys = [
                b"NumberBox",
                b"7.7.3",
                b"android", 
                self.phone.encode(),
                b"SM-A505F",
                b"okhttp/4.12.0"
            ]
            
            for key in xor_keys:
                xor_result = self.xor_decrypt(decoded, key)
                if self.contains_phone_number(xor_result):
                    results[f"xor_{key.decode('utf-8', errors='ignore')}"] = {
                        "success": True,
                        "preview": xor_result[:100].decode('utf-8', errors='ignore')
                    }
            
            # محاولة 2: Caesar cipher للبايتات
            for shift in [1, 7, 13, 64, 128]:
                caesar_result = bytes((b + shift) % 256 for b in decoded)
                if self.contains_phone_number(caesar_result):
                    results[f"caesar_shift_{shift}"] = {
                        "success": True,
                        "preview": caesar_result[:100].hex()
                    }
            
            # محاولة 3: استبدال البايتات (substitution)
            reversed_result = bytes(reversed(decoded))
            if self.contains_phone_number(reversed_result):
                results["byte_reversal"] = {
                    "success": True,
                    "preview": reversed_result[:100].hex()
                }
            
            return results
            
        except Exception as e:
            return {"error": str(e)}
    
    def xor_decrypt(self, data: bytes, key: bytes) -> bytes:
        """فك تشفير XOR"""
        result = bytearray()
        key_len = len(key)
        
        for i, byte in enumerate(data):
            result.append(byte ^ key[i % key_len])
            
        return bytes(result)
    
    def contains_phone_number(self, data: bytes) -> bool:
        """فحص إذا كانت البيانات تحتوي على رقم الهاتف"""
        try:
            text = data.decode('utf-8', errors='ignore')
            phone_variations = [
                self.phone,
                self.phone[1:],
                self.phone.replace("+964", "0"),
                "".join(filter(str.isdigit, self.phone))
            ]
            
            return any(variation in text for variation in phone_variations)
        except:
            # إذا فشل التحويل لنص، فحص البايتات مباشرة
            phone_bytes = [
                self.phone.encode(),
                self.phone[1:].encode(),
                "".join(filter(str.isdigit, self.phone)).encode()
            ]
            
            return any(phone in data for phone in phone_bytes)

def main():
    """تشغيل التحليل المتقدم"""
    
    decryptor = NumberBoxDecryptor()
    
    print("🔍 بدء التحليل المتقدم لتشفير NumberBox...")
    print("=" * 60)
    
    # تحليل بنية number
    number_analysis = decryptor.analyze_number_structure()
    print("📊 تحليل بنية number:")
    print(json.dumps(number_analysis, indent=2, ensure_ascii=False))
    print("=" * 60)
    
    # محاولة فك التشفير البسيط
    decryption_attempts = decryptor.attempt_simple_decryption_methods()
    print("🔓 محاولات فك التشفير:")
    print(json.dumps(decryption_attempts, indent=2, ensure_ascii=False))
    
    return number_analysis, decryption_attempts

if __name__ == "__main__":
    main()