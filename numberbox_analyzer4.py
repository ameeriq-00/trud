"""
فك التشفير المتقدم - معالجة النتائج الناجحة
"""

import base64
import json
import zlib
import gzip
import bz2
from typing import Dict, List

class AdvancedDecryptor:
    def __init__(self):
        self.phone = "+9647809394930"
        
        # المفاتيح الناجحة من التحليل السابق
        self.successful_keys = [
            "android",
            "+9647809394930", 
            "9647809394930",
            "com.hotcodes.numberbox",
            "34",
            "com.hotcodes.numberbox_7.7.3",
            "5364153498",
            "258c26488bd782ff",
            "9af9a82c4b5c26d2917d628e16bd886d",
            "2c8c413703331422"
        ]
    
    def deep_decrypt_with_compression(self, encrypted_data: str) -> Dict:
        """فك التشفير مع تجربة طرق الضغط المختلفة"""
        
        try:
            decoded = base64.b64decode(encrypted_data)
        except:
            return {"error": "Failed to decode base64"}
        
        results = {}
        
        for key in self.successful_keys:
            print(f"🔍 تحليل المفتاح: {key}")
            
            # فك XOR
            xor_data = self.xor_decrypt(decoded, key.encode())
            
            # محاولة فك الضغط بطرق مختلفة
            decompression_results = self.try_all_decompression_methods(xor_data)
            
            # تحليل النتائج
            analysis = self.analyze_decrypted_data(xor_data, decompression_results)
            
            if analysis['found_phone_data'] or analysis['found_json']:
                results[key] = {
                    "xor_result": xor_data[:100].hex(),
                    "decompression": decompression_results,
                    "analysis": analysis,
                    "success": True
                }
                
                # إذا وجدنا JSON صالح، اطبعه
                if analysis['found_json']:
                    print(f"✅ وجدنا JSON! المفتاح: {key}")
                    print(f"JSON: {analysis['json_data']}")
                    
        return results
    
    def xor_decrypt(self, data: bytes, key: bytes) -> bytes:
        """فك تشفير XOR"""
        result = bytearray()
        key_len = len(key)
        
        for i, byte in enumerate(data):
            result.append(byte ^ key[i % key_len])
            
        return bytes(result)
    
    def try_all_decompression_methods(self, data: bytes) -> Dict:
        """تجربة جميع طرق فك الضغط"""
        
        methods = {
            "zlib": self.try_zlib_decompress,
            "gzip": self.try_gzip_decompress, 
            "bz2": self.try_bz2_decompress,
            "deflate": self.try_deflate_decompress
        }
        
        results = {}
        
        for method_name, method_func in methods.items():
            try:
                decompressed = method_func(data)
                if decompressed:
                    results[method_name] = {
                        "success": True,
                        "size": len(decompressed),
                        "preview": decompressed[:200].decode('utf-8', errors='ignore'),
                        "hex_preview": decompressed[:50].hex(),
                        "full_data": decompressed
                    }
                else:
                    results[method_name] = {"success": False}
            except Exception as e:
                results[method_name] = {"success": False, "error": str(e)}
        
        return results
    
    def try_zlib_decompress(self, data: bytes) -> bytes:
        """محاولة فك ضغط zlib"""
        try:
            return zlib.decompress(data)
        except:
            # محاولة مع تجاهل header
            try:
                return zlib.decompress(data, -15)  # raw deflate
            except:
                return None
    
    def try_gzip_decompress(self, data: bytes) -> bytes:
        """محاولة فك ضغط gzip"""
        try:
            return gzip.decompress(data)
        except:
            return None
    
    def try_bz2_decompress(self, data: bytes) -> bytes:
        """محاولة فك ضغط bz2"""
        try:
            return bz2.decompress(data)
        except:
            return None
    
    def try_deflate_decompress(self, data: bytes) -> bytes:
        """محاولة فك ضغط deflate"""
        try:
            # محاولة deflate خام
            return zlib.decompress(data, -zlib.MAX_WBITS)
        except:
            return None
    
    def analyze_decrypted_data(self, xor_data: bytes, decompression_results: Dict) -> Dict:
        """تحليل البيانات المفكوكة"""
        
        analysis = {
            "found_phone_data": False,
            "found_json": False,
            "phone_locations": [],
            "json_data": None,
            "text_content": None,
            "contains_readable_text": False
        }
        
        # تحليل XOR data مباشرة
        analysis.update(self.analyze_single_data(xor_data))
        
        # تحليل البيانات المفكوكة الضغط
        for method, result in decompression_results.items():
            if result.get("success", False):
                decompressed_data = result["full_data"]
                decompressed_analysis = self.analyze_single_data(decompressed_data)
                
                # إذا وجدنا بيانات أفضل في المفكوك الضغط
                if decompressed_analysis["found_json"] or decompressed_analysis["found_phone_data"]:
                    analysis.update(decompressed_analysis)
                    analysis["decompression_method"] = method
                    break
        
        return analysis
    
    def analyze_single_data(self, data: bytes) -> Dict:
        """تحليل مجموعة بيانات واحدة"""
        
        analysis = {
            "found_phone_data": False,
            "found_json": False,
            "phone_locations": [],
            "json_data": None,
            "text_content": None,
            "contains_readable_text": False
        }
        
        try:
            # محاولة تحويل لنص
            text = data.decode('utf-8', errors='ignore')
            analysis["text_content"] = text[:500]  # أول 500 حرف
            
            # فحص إذا كان النص قابل للقراءة
            printable_ratio = sum(1 for c in text[:100] if c.isprintable()) / min(len(text), 100)
            analysis["contains_readable_text"] = printable_ratio > 0.7
            
            # البحث عن رقم الهاتف
            phone_patterns = [
                "+9647809394930",
                "9647809394930", 
                "7809394930",
                "964", "780", "939", "493", "930"
            ]
            
            found_patterns = []
            for pattern in phone_patterns:
                if pattern in text:
                    found_patterns.append(pattern)
                    analysis["phone_locations"].append({
                        "pattern": pattern,
                        "position": text.find(pattern)
                    })
            
            if found_patterns:
                analysis["found_phone_data"] = True
            
            # فحص JSON
            if '{' in text and '}' in text:
                # محاولة parse JSON
                try:
                    # البحث عن JSON objects
                    start = text.find('{')
                    end = text.rfind('}') + 1
                    
                    if start >= 0 and end > start:
                        json_candidate = text[start:end]
                        parsed_json = json.loads(json_candidate)
                        analysis["found_json"] = True
                        analysis["json_data"] = parsed_json
                        
                except json.JSONDecodeError:
                    # محاولة البحث عن JSON جزئي
                    if '"' in text and ':' in text:
                        analysis["found_json"] = "partial"
                        
        except Exception as e:
            analysis["decode_error"] = str(e)
        
        return analysis
    
    def find_best_decryption_result(self, results: Dict) -> Dict:
        """العثور على أفضل نتيجة فك تشفير"""
        
        best_result = None
        best_score = 0
        
        for key, result in results.items():
            if not result.get("success", False):
                continue
                
            analysis = result["analysis"]
            score = 0
            
            # نقاط للعثور على JSON
            if analysis.get("found_json", False):
                score += 50
                if isinstance(analysis["json_data"], dict):
                    score += 30
            
            # نقاط للعثور على رقم الهاتف  
            if analysis.get("found_phone_data", False):
                score += 40
                score += len(analysis.get("phone_locations", [])) * 10
            
            # نقاط للنص القابل للقراءة
            if analysis.get("contains_readable_text", False):
                score += 20
            
            if score > best_score:
                best_score = score
                best_result = {
                    "key": key,
                    "score": score,
                    "result": result
                }
        
        return best_result

def main():
    """تشغيل فك التشفير المتقدم"""
    
    # ضع البيانات المشفرة هنا
    encrypted_data = "[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]"
    
    if encrypted_data == "[ENCRYPTED_DATA_PLACEHOLDER]":
        print("⚠️ ضع البيانات المشفرة في encrypted_data")
        return
    
    decryptor = AdvancedDecryptor()
    
    print("🔓 بدء فك التشفير المتقدم...")
    print("=" * 60)
    
    # فك التشفير مع الضغط
    results = decryptor.deep_decrypt_with_compression(encrypted_data)
    
    print("\n" + "=" * 60)
    print("📊 نتائج فك التشفير:")
    
    for key, result in results.items():
        if result.get("success", False):
            analysis = result["analysis"]
            print(f"\n🔑 المفتاح: {key}")
            
            if analysis.get("found_json", False):
                print("  ✅ وجدنا JSON!")
                if isinstance(analysis["json_data"], dict):
                    print("  📄 JSON صالح:")
                    print(json.dumps(analysis["json_data"], indent=4, ensure_ascii=False))
            
            if analysis.get("found_phone_data", False):
                print("  📞 وجدنا بيانات الهاتف!")
                for location in analysis["phone_locations"]:
                    print(f"    - {location['pattern']} في الموقع {location['position']}")
            
            if analysis.get("contains_readable_text", False):
                print("  📝 نص قابل للقراءة:")
                print(f"    {analysis['text_content'][:200]}...")
    
    # العثور على أفضل نتيجة
    best = decryptor.find_best_decryption_result(results)
    if best:
        print(f"\n🏆 أفضل نتيجة: المفتاح '{best['key']}' (نقاط: {best['score']})")
    
    return results

if __name__ == "__main__":
    main()