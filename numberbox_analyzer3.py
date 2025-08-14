"""
استخراج مفاتيح التشفير المحتملة من HAR File
بناءً على الاكتشافات السابقة
"""

import json
import base64
import hashlib
import hmac
from typing import Dict, List

class HARKeyExtractor:
    def __init__(self, har_file_path: str = None):
        self.phone = "+9647809394930"
        
        # البيانات من HAR file - يمكن تحديثها
        self.har_data = {
            "device_info": {
                "model": "SM-A505F",
                "version": "7.7.3", 
                "user_agent": "okhttp/4.12.0",
                "device": "android",
                "android_api_level": 30
            },
            "app_info": {
                "package": "com.hotcodes.numberbox",
                "app_id": "ca-app-pub-9725931532481885~5364153498",
                "version_code": "34"
            },
            "device_ids": {
                "advertising_id": "2f00dac566eab05ed7b1682299be488a",
                "install_id": "1:627989477950:android:bd4371c426c6ee03962f6f"
            },
            "request_params": {
                "ms": "CoACbupql_uekn0Z8Q8T0sThM_bBtHKxXn0J2QJOqKA87ajal2TVZpi...",  # طويل جداً
                "blob": "ABPQqLFMSDbvIcEPYCK2xONDt5kFv7wS0nyYjyPP2vIv_lX2ya31_FojIhoTakBM0Dw1nF9jgeLvyiqxL2Pdm527ufYuTMu7rQUgcu8u7DDZMZbG9fPWxqUpB-IusAy8m4794uSTTyug2x5Yi4b730JNi5smq6Ay5YvhY8ZNef2Upz1IRgDQh6Zxs7cjXQOCirILJYrHzwzEvv5phe1N-VrehqUqpgVpSIrd0y9nt3gY6BT7iBnERv7TKt6cQqxH2UWjHn-Oybxu3s6Mnd-sYDELKqTIbbwKC-zOEDax5heKTAGi3ybYG6Ij1VEp-XIAI48IHvsJ3XU6davG49SpcKfBG7Q1c1LsDuEscaoKWEMEwH5wAM9EV7KywFVchrpzadEeiYmmL8YJpMOCyikws3eAgboL38Ob5KgkzGyH7f5ntyTfa74cmUzaNbxMIw"
            }
        }
    
    def generate_potential_keys(self) -> Dict[str, List[str]]:
        """توليد المفاتيح المحتملة من البيانات المتاحة"""
        
        keys = {
            "simple_strings": [],
            "device_based": [],
            "app_based": [], 
            "hash_based": [],
            "combined_keys": [],
            "blob_derived": []
        }
        
        # 1. Simple string keys
        keys["simple_strings"] = [
            "NumberBox",
            "7.7.3",
            "android", 
            "okhttp/4.12.0",
            "SM-A505F",
            self.phone,
            self.phone[1:],  # بدون +
            "com.hotcodes.numberbox"
        ]
        
        # 2. Device-based keys
        keys["device_based"] = [
            self.har_data["device_ids"]["advertising_id"],
            self.har_data["device_ids"]["install_id"],
            self.har_data["app_info"]["app_id"],
            self.har_data["device_info"]["model"],
            f"{self.har_data['device_info']['model']}_{self.har_data['device_info']['version']}"
        ]
        
        # 3. App-based keys
        keys["app_based"] = [
            self.har_data["app_info"]["package"],
            self.har_data["app_info"]["version_code"],
            f"{self.har_data['app_info']['package']}_{self.har_data['device_info']['version']}",
            "ca-app-pub-9725931532481885",
            "5364153498"
        ]
        
        # 4. Hash-based keys
        phone_hash_sources = [
            self.phone,
            self.phone + self.har_data["device_info"]["version"],
            self.phone + self.har_data["device_ids"]["advertising_id"][:8],
            self.phone + "NumberBox"
        ]
        
        for source in phone_hash_sources:
            keys["hash_based"].extend([
                hashlib.md5(source.encode()).hexdigest()[:16],  # أول 16 حرف
                hashlib.sha1(source.encode()).hexdigest()[:16],
                hashlib.sha256(source.encode()).hexdigest()[:32]
            ])
        
        # 5. Combined keys
        keys["combined_keys"] = [
            f"{self.phone}_{self.har_data['device_info']['version']}",
            f"{self.har_data['device_info']['model']}_{self.phone[1:]}",
            f"NumberBox_{self.phone[1:]}",
            f"{self.har_data['device_ids']['advertising_id'][:8]}_{self.phone[-4:]}"
        ]
        
        # 6. Blob-derived keys (من أول وآخر جزء من blob)
        blob = self.har_data["request_params"]["blob"]
        if len(blob) > 32:
            keys["blob_derived"] = [
                blob[:16],  # أول 16 حرف
                blob[-16:], # آخر 16 حرف
                blob[16:32], # وسط
                blob[:8] + blob[-8:]  # أول وآخر 8
            ]
        
        return keys
    
    def test_keys_against_encrypted_data(self, encrypted_number: str) -> Dict:
        """اختبار المفاتيح ضد البيانات المشفرة"""
        
        try:
            decoded_data = base64.b64decode(encrypted_number)
        except:
            return {"error": "Failed to decode base64"}
        
        potential_keys = self.generate_potential_keys()
        results = {}
        
        for category, keys in potential_keys.items():
            results[category] = []
            
            for key in keys:
                if not key:
                    continue
                    
                try:
                    # تجربة XOR
                    xor_result = self.xor_decrypt(decoded_data, key.encode())
                    if self.looks_like_phone_data(xor_result):
                        results[category].append({
                            "key": key,
                            "method": "xor",
                            "success": True,
                            "preview": xor_result[:100].decode('utf-8', errors='ignore')
                        })
                    
                    # تجربة كـ AES key (16 bytes)
                    if len(key) >= 16:
                        aes_key = key.encode()[:16]
                        # هنا يمكن إضافة AES decryption لاحقاً
                        
                except Exception as e:
                    continue
        
        return results
    
    def xor_decrypt(self, data: bytes, key: bytes) -> bytes:
        """فك تشفير XOR"""
        result = bytearray()
        key_len = len(key)
        
        for i, byte in enumerate(data):
            result.append(byte ^ key[i % key_len])
            
        return bytes(result)
    
    def looks_like_phone_data(self, data: bytes) -> bool:
        """فحص إذا كانت البيانات تبدو وكأنها تحتوي على رقم الهاتف"""
        
        try:
            # محاولة كـ text
            text = data.decode('utf-8', errors='ignore')
            
            # البحث عن أجزاء من رقم الهاتف
            phone_parts = ["964", "780", "939", "493", "930"]
            
            found_parts = sum(1 for part in phone_parts if part in text)
            
            # إذا وجدنا 2+ أجزاء، احتمال كبير
            if found_parts >= 2:
                return True
                
            # فحص إذا كان يحتوي على JSON structure
            if any(marker in text for marker in ['{"', '"}', '":', '","']):
                return True
                
        except:
            pass
        
        # فحص البايتات مباشرة
        phone_bytes = [
            b"964", b"780", b"939", b"493", b"930",
            self.phone[1:].encode(),  # الرقم بدون +
            b"+964"
        ]
        
        found_bytes = sum(1 for phone_byte in phone_bytes if phone_byte in data)
        
        return found_bytes >= 1
    
    def analyze_blob_parameter(self) -> Dict:
        """تحليل معامل blob الذي قد يحتوي على مفاتيح"""
        
        blob = self.har_data["request_params"]["blob"]
        
        try:
            # محاولة فك base64
            decoded_blob = base64.b64decode(blob)
            
            analysis = {
                "blob_length": len(blob),
                "decoded_length": len(decoded_blob),
                "first_bytes": decoded_blob[:20].hex(),
                "last_bytes": decoded_blob[-20:].hex(),
                "contains_phone_hints": self.search_phone_hints_in_blob(decoded_blob),
                "potential_key_sections": self.extract_key_sections_from_blob(decoded_blob)
            }
            
            return analysis
            
        except Exception as e:
            return {"error": f"Failed to analyze blob: {str(e)}"}
    
    def search_phone_hints_in_blob(self, blob_data: bytes) -> Dict:
        """البحث عن تلميحات الهاتف في blob"""
        
        hints = {
            "country_code": b"964" in blob_data,
            "phone_parts": [],
            "positions": []
        }
        
        # البحث عن أجزاء من الرقم
        phone_parts = ["964", "780", "939", "493", "930"]
        
        for part in phone_parts:
            part_bytes = part.encode()
            if part_bytes in blob_data:
                pos = blob_data.find(part_bytes)
                hints["phone_parts"].append(part)
                hints["positions"].append(pos)
        
        return hints
    
    def extract_key_sections_from_blob(self, blob_data: bytes) -> List[str]:
        """استخراج أقسام محتملة كمفاتيح من blob"""
        
        key_sections = []
        
        # تقسيم لأجزاء بأطوال مفاتيح شائعة
        key_lengths = [8, 16, 24, 32]
        
        for length in key_lengths:
            # من البداية
            if len(blob_data) >= length:
                key_sections.append(blob_data[:length].hex())
            
            # من النهاية  
            if len(blob_data) >= length:
                key_sections.append(blob_data[-length:].hex())
            
            # من الوسط
            if len(blob_data) >= length * 2:
                mid = len(blob_data) // 2
                key_sections.append(blob_data[mid:mid+length].hex())
        
        return key_sections[:10]  # أول 10 فقط

def main():
    """تشغيل استخراج المفاتيح"""
    
    extractor = HARKeyExtractor()
    
    print("🔑 استخراج المفاتيح المحتملة من HAR file...")
    print("=" * 60)
    
    # توليد المفاتيح
    keys = extractor.generate_potential_keys()
    print("📝 المفاتيح المحتملة:")
    for category, key_list in keys.items():
        print(f"\n{category}: {len(key_list)} مفاتيح")
        for i, key in enumerate(key_list[:3]):  # أول 3 فقط للعرض
            print(f"  {i+1}. {key}")
        if len(key_list) > 3:
            print(f"  ... و {len(key_list)-3} مفاتيح أخرى")
    
    print("\n" + "=" * 60)
    
    # اختبار المفاتيح مع البيانات المشفرة
    encrypted_number = "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"  # ضع البيانات المشفرة هنا
    
    if encrypted_number != "[ENCRYPTED_DATA_PLACEHOLDER]":
        print("🔍 اختبار المفاتيح مع البيانات المشفرة...")
        results = extractor.test_keys_against_encrypted_data(encrypted_number)
        
        successful_keys = []
        for category, tests in results.items():
            if tests:
                print(f"\n🔑 {category}:")
                for test in tests:
                    if test.get('success', False):
                        print(f"  ✅ المفتاح: {test['key']}")
                        print(f"     النتيجة: {test['preview'][:100]}...")
                        successful_keys.append(test)
        
        if successful_keys:
            print(f"\n🎯 تم العثور على {len(successful_keys)} مفاتيح ناجحة!")
        else:
            print("\n⚠️ لم يتم العثور على مفاتيح ناجحة")
    else:
        print("\n⚠️ ضع البيانات المشفرة في encrypted_number لاختبار المفاتيح")
    
    return keys

if __name__ == "__main__":
    main()