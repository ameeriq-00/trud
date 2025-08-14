"""
استخراج البيانات النهائي - البحث عن JSON صحيح ورقم الهاتف
"""

import base64
import json
import re
from typing import Dict, List

class FinalDataExtractor:
    def __init__(self):
        self.phone = "+9647809394930"
        
        # أفضل المفاتيح من التحليل السابق
        self.best_keys = [
            "android",
            "+9647809394930", 
            "9647809394930",
            "com.hotcodes.numberbox",
            "34"
        ]
    
    def extract_meaningful_data(self, encrypted_data: str) -> Dict:
        """استخراج البيانات المفيدة من جميع المفاتيح"""
        
        try:
            decoded = base64.b64decode(encrypted_data)
        except:
            return {"error": "Failed to decode base64"}
        
        results = {}
        
        for key in self.best_keys:
            print(f"🔍 تحليل عميق للمفتاح: {key}")
            
            # فك XOR
            xor_data = self.xor_decrypt(decoded, key.encode())
            
            # استخراج البيانات المفيدة
            extracted = self.extract_from_decrypted_data(xor_data, key)
            
            if extracted['has_useful_data']:
                results[key] = extracted
                
                # طباعة النتائج المفيدة فوراً
                self.print_useful_findings(key, extracted)
        
        return results
    
    def xor_decrypt(self, data: bytes, key: bytes) -> bytes:
        """فك تشفير XOR"""
        result = bytearray()
        key_len = len(key)
        
        for i, byte in enumerate(data):
            result.append(byte ^ key[i % key_len])
            
        return bytes(result)
    
    def extract_from_decrypted_data(self, data: bytes, key: str) -> Dict:
        """استخراج البيانات المفيدة من البيانات المفكوكة"""
        
        result = {
            'key': key,
            'has_useful_data': False,
            'phone_numbers': [],
            'json_objects': [],
            'readable_strings': [],
            'hex_patterns': [],
            'file_structure': None
        }
        
        try:
            # تحويل لنص مع تجاهل الأخطاء
            text = data.decode('utf-8', errors='replace')
            
            # 1. البحث عن أرقام الهواتف
            phone_patterns = [
                r'\+?964\d{10}',  # الرقم الكامل
                r'964\d{10}',
                r'780\d{7}',      # الجزء المحلي
                r'939\d{4}',
                r'\d{11,13}'      # أرقام طويلة
            ]
            
            for pattern in phone_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    if match not in result['phone_numbers']:
                        result['phone_numbers'].append(match)
            
            # 2. البحث عن JSON objects صحيحة
            json_candidates = self.find_json_candidates(text)
            for candidate in json_candidates:
                try:
                    parsed = json.loads(candidate)
                    result['json_objects'].append(parsed)
                except:
                    # محاولة إصلاح JSON
                    fixed = self.try_fix_json(candidate)
                    if fixed:
                        result['json_objects'].append(fixed)
            
            # 3. البحث عن strings قابلة للقراءة
            readable = self.extract_readable_strings(text)
            result['readable_strings'] = readable
            
            # 4. تحليل البيانات كـ binary structure
            binary_analysis = self.analyze_binary_structure(data)
            result['file_structure'] = binary_analysis
            
            # 5. البحث عن patterns مهمة في hex
            hex_patterns = self.find_important_hex_patterns(data)
            result['hex_patterns'] = hex_patterns
            
            # تحديد إذا كان لدينا بيانات مفيدة
            if (result['phone_numbers'] or 
                result['json_objects'] or 
                len(result['readable_strings']) > 5 or
                result['file_structure']['likely_format'] != 'unknown'):
                
                result['has_useful_data'] = True
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def find_json_candidates(self, text: str) -> List[str]:
        """البحث عن JSON candidates في النص"""
        
        candidates = []
        
        # البحث عن نمط JSON بسيط
        json_pattern = r'\{[^{}]*\}'
        matches = re.findall(json_pattern, text)
        candidates.extend(matches)
        
        # البحث عن JSON متداخل
        stack = []
        start = -1
        
        for i, char in enumerate(text):
            if char == '{':
                if not stack:
                    start = i
                stack.append(char)
            elif char == '}' and stack:
                stack.pop()
                if not stack and start >= 0:
                    candidate = text[start:i+1]
                    if len(candidate) > 10:  # تجاهل JSON الصغير جداً
                        candidates.append(candidate)
        
        return candidates
    
    def try_fix_json(self, json_str: str) -> dict:
        """محاولة إصلاح JSON التالف"""
        
        fixes = [
            # إصلاح quotes
            lambda s: s.replace("'", '"'),
            # إصلاح trailing commas
            lambda s: re.sub(r',\s*}', '}', s),
            lambda s: re.sub(r',\s*]', ']', s),
            # إضافة quotes للمفاتيح
            lambda s: re.sub(r'(\w+):', r'"\1":', s)
        ]
        
        for fix in fixes:
            try:
                fixed = fix(json_str)
                return json.loads(fixed)
            except:
                continue
        
        return None
    
    def extract_readable_strings(self, text: str, min_length: int = 4) -> List[str]:
        """استخراج النصوص القابلة للقراءة"""
        
        # البحث عن strings طويلة قابلة للقراءة
        pattern = r'[a-zA-Z0-9\s\-_\.@]{' + str(min_length) + ',}'
        matches = re.findall(pattern, text)
        
        # فلترة النتائج المفيدة
        useful_strings = []
        for match in matches:
            # تجاهل الstrings المليئة بالمسافات أو الرموز
            if len(match.strip()) >= min_length and not match.isspace():
                useful_strings.append(match.strip())
        
        # إزالة المكررات وترتيب حسب الطول
        unique_strings = list(set(useful_strings))
        return sorted(unique_strings, key=len, reverse=True)[:20]  # أول 20
    
    def analyze_binary_structure(self, data: bytes) -> Dict:
        """تحليل البنية الثنائية للبيانات"""
        
        analysis = {
            'size': len(data),
            'entropy': self.calculate_entropy(data),
            'likely_format': 'unknown',
            'headers': [],
            'null_bytes': data.count(0),
            'printable_ratio': sum(1 for b in data if 32 <= b <= 126) / len(data)
        }
        
        # فحص headers شائعة
        if data.startswith(b'PK'):
            analysis['likely_format'] = 'ZIP/JAR'
        elif data.startswith(b'\x1f\x8b'):
            analysis['likely_format'] = 'GZIP'
        elif data.startswith(b'BZ'):
            analysis['likely_format'] = 'BZIP2'
        elif data.startswith(b'{\x22') or b'{"' in data[:100]:
            analysis['likely_format'] = 'JSON'
        elif analysis['printable_ratio'] > 0.8:
            analysis['likely_format'] = 'TEXT'
        elif analysis['entropy'] > 7.5:
            analysis['likely_format'] = 'ENCRYPTED/COMPRESSED'
        
        return analysis
    
    def calculate_entropy(self, data: bytes) -> float:
        """حساب entropy"""
        if not data:
            return 0
        
        byte_counts = [0] * 256
        for byte in data:
            byte_counts[byte] += 1
        
        import math
        entropy = 0
        data_len = len(data)
        for count in byte_counts:
            if count > 0:
                p = count / data_len
                entropy -= p * math.log2(p)
        
        return entropy
    
    def find_important_hex_patterns(self, data: bytes) -> List[Dict]:
        """البحث عن patterns مهمة في البيانات hex"""
        
        patterns = []
        hex_data = data.hex()
        
        # البحث عن أنماط الهاتف في hex
        phone_hex_patterns = [
            '393634',  # "964" 
            '373830',  # "780"
            '393339',  # "939"
        ]
        
        for pattern in phone_hex_patterns:
            if pattern in hex_data:
                pos = hex_data.find(pattern)
                patterns.append({
                    'pattern': pattern,
                    'decoded': bytes.fromhex(pattern).decode(),
                    'position': pos // 2,
                    'context': hex_data[max(0, pos-20):pos+len(pattern)+20]
                })
        
        return patterns
    
    def print_useful_findings(self, key: str, extracted: Dict):
        """طباعة النتائج المفيدة فوراً"""
        
        print(f"\n🔑 نتائج المفتاح: {key}")
        print("-" * 40)
        
        if extracted['phone_numbers']:
            print("📞 أرقام الهواتف المكتشفة:")
            for phone in extracted['phone_numbers']:
                print(f"  ✅ {phone}")
        
        if extracted['json_objects']:
            print("📄 JSON Objects:")
            for i, obj in enumerate(extracted['json_objects']):
                print(f"  📋 JSON {i+1}:")
                print(json.dumps(obj, indent=4, ensure_ascii=False))
        
        if extracted['readable_strings']:
            print("📝 نصوص قابلة للقراءة:")
            for i, string in enumerate(extracted['readable_strings'][:5]):  # أول 5
                print(f"  {i+1}. {string}")
        
        if extracted['hex_patterns']:
            print("🔍 أنماط hex مهمة:")
            for pattern in extracted['hex_patterns']:
                print(f"  📍 {pattern['decoded']} في الموقع {pattern['position']}")
        
        structure = extracted['file_structure']
        if structure and structure['likely_format'] != 'unknown':
            print(f"📂 نوع البيانات المحتمل: {structure['likely_format']}")
            print(f"   📊 Entropy: {structure['entropy']:.2f}")
            print(f"   📝 نسبة النص: {structure['printable_ratio']:.2%}")

def main():
    """تشغيل الاستخراج النهائي"""
    
    # ضع البيانات المشفرة هنا
    encrypted_data = "[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]"
    
    if encrypted_data == "[ENCRYPTED_DATA_PLACEHOLDER]":
        print("⚠️ ضع البيانات المشفرة في encrypted_data")
        return
    
    extractor = FinalDataExtractor()
    
    print("🎯 بدء الاستخراج النهائي للبيانات...")
    print("=" * 70)
    
    results = extractor.extract_meaningful_data(encrypted_data)
    
    print("\n" + "=" * 70)
    print("🏆 ملخص النتائج النهائية:")
    
    total_phones = sum(len(r['phone_numbers']) for r in results.values())
    total_json = sum(len(r['json_objects']) for r in results.values())
    
    print(f"📞 إجمالي أرقام الهواتف: {total_phones}")
    print(f"📄 إجمالي JSON objects: {total_json}")
    print(f"🔑 عدد المفاتيح الناجحة: {len(results)}")
    
    # أفضل نتيجة
    if results:
        best_key = max(results.keys(), 
                      key=lambda k: len(results[k]['phone_numbers']) + len(results[k]['json_objects']))
        print(f"\n🏅 أفضل مفتاح: {best_key}")
    
    return results

if __name__ == "__main__":
    main()