"""
تحليل المفاتيح الواعدة نهائياً وفك البيانات الكامل
"""

import base64
import json
import zlib
import gzip
import re
from typing import Dict, List

class FinalKeyAnalysis:
    def __init__(self):
        self.phone = "+9647809394930"
        
        # المفاتيح الواعدة من التحليل السابق
        self.promising_keys = [
            {
                "name": "ccode_start",
                "hex": "76183b2852881d53cf603a0824f4c49b",
                "key": bytes.fromhex("76183b2852881d53cf603a0824f4c49b")
            },
            {
                "name": "advertising_id_derived", 
                "hex": "9761098411e9a86c842cd023f8e3e9cb",
                "key": bytes.fromhex("9761098411e9a86c842cd023f8e3e9cb")
            }
        ]
    
    def deep_analysis_of_keys(self, encrypted_data: str) -> Dict:
        """تحليل عميق للمفاتيح الواعدة"""
        
        try:
            data = base64.b64decode(encrypted_data)
        except:
            return {"error": "Failed to decode base64"}
        
        results = {}
        
        for key_info in self.promising_keys:
            print(f"\n🔍 تحليل عميق للمفتاح: {key_info['name']}")
            print("-" * 50)
            
            key = key_info["key"]
            
            # فك XOR
            xor_result = self.xor_decrypt(data, key)
            
            # تحليل شامل
            analysis = self.comprehensive_analysis(xor_result, key_info["name"])
            
            results[key_info["name"]] = {
                "key_info": key_info,
                "xor_result": xor_result,
                "analysis": analysis
            }
            
            # طباعة النتائج
            self.print_analysis_results(key_info["name"], analysis)
        
        return results
    
    def xor_decrypt(self, data: bytes, key: bytes) -> bytes:
        """فك تشفير XOR"""
        result = bytearray()
        key_len = len(key)
        
        for i, byte in enumerate(data):
            result.append(byte ^ key[i % key_len])
            
        return bytes(result)
    
    def comprehensive_analysis(self, data: bytes, key_name: str) -> Dict:
        """تحليل شامل للبيانات المفكوكة"""
        
        analysis = {
            "key_name": key_name,
            "data_size": len(data),
            "raw_analysis": {},
            "decompression_attempts": {},
            "phone_search": {},
            "json_extraction": {},
            "text_analysis": {},
            "final_verdict": {}
        }
        
        # 1. تحليل البيانات الخام
        analysis["raw_analysis"] = self.analyze_raw_data(data)
        
        # 2. محاولات فك الضغط
        analysis["decompression_attempts"] = self.try_decompress_all_methods(data)
        
        # 3. البحث عن رقم الهاتف
        analysis["phone_search"] = self.comprehensive_phone_search(data)
        
        # 4. استخراج JSON
        analysis["json_extraction"] = self.extract_json_data(data)
        
        # 5. تحليل النص
        analysis["text_analysis"] = self.analyze_text_content(data)
        
        # 6. الحكم النهائي
        analysis["final_verdict"] = self.make_final_verdict(analysis)
        
        return analysis
    
    def analyze_raw_data(self, data: bytes) -> Dict:
        """تحليل البيانات الخام"""
        
        analysis = {
            "entropy": self.calculate_entropy(data),
            "null_bytes": data.count(0),
            "printable_ratio": sum(1 for b in data if 32 <= b <= 126) / len(data),
            "first_32_bytes": data[:32].hex(),
            "last_32_bytes": data[-32:].hex(),
            "suspected_format": None
        }
        
        # تحديد النوع المحتمل
        if analysis["entropy"] < 6:
            analysis["suspected_format"] = "plaintext_or_simple_encoding"
        elif 6 <= analysis["entropy"] < 7.5:
            analysis["suspected_format"] = "compressed_or_encoded"
        else:
            analysis["suspected_format"] = "encrypted_or_random"
        
        return analysis
    
    def try_decompress_all_methods(self, data: bytes) -> Dict:
        """محاولة جميع طرق فك الضغط"""
        
        methods = {
            "zlib": self.try_zlib,
            "gzip": self.try_gzip,
            "deflate": self.try_deflate,
            "bz2": self.try_bz2
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
                        "contains_phone": self.phone[1:] in decompressed.decode('utf-8', errors='ignore'),
                        "full_data": decompressed
                    }
                    
                    # إذا وجدنا رقم الهاتف، هذا نجاح كبير!
                    if results[method_name]["contains_phone"]:
                        print(f"🎯 نجاح! وجدنا رقم الهاتف في {method_name}!")
                        
                else:
                    results[method_name] = {"success": False}
            except Exception as e:
                results[method_name] = {"success": False, "error": str(e)}
        
        return results
    
    def try_zlib(self, data: bytes) -> bytes:
        """محاولة zlib"""
        try:
            return zlib.decompress(data)
        except:
            try:
                return zlib.decompress(data, -15)  # raw deflate
            except:
                return None
    
    def try_gzip(self, data: bytes) -> bytes:
        """محاولة gzip"""
        try:
            return gzip.decompress(data)
        except:
            return None
    
    def try_deflate(self, data: bytes) -> bytes:
        """محاولة deflate"""
        try:
            return zlib.decompress(data, -zlib.MAX_WBITS)
        except:
            return None
    
    def try_bz2(self, data: bytes) -> bytes:
        """محاولة bz2"""
        try:
            import bz2
            return bz2.decompress(data)
        except:
            return None
    
    def comprehensive_phone_search(self, data: bytes) -> Dict:
        """البحث الشامل عن رقم الهاتف"""
        
        search_results = {
            "raw_bytes": False,
            "utf8_text": False,
            "ascii_text": False,
            "hex_patterns": [],
            "found_numbers": []
        }
        
        # البحث في البايتات الخام
        phone_patterns_bytes = [
            self.phone.encode(),
            self.phone[1:].encode(),  # بدون +
            b"964", b"780", b"939", b"493", b"930"
        ]
        
        for pattern in phone_patterns_bytes:
            if pattern in data:
                search_results["raw_bytes"] = True
                search_results["found_numbers"].append(pattern.decode())
        
        # البحث في النص
        try:
            text = data.decode('utf-8', errors='ignore')
            phone_regex = [
                r'\+?964\d{10}',
                r'964\d{10}', 
                r'780\d{7}',
                r'939\d{4}',
                r'\d{11,13}'
            ]
            
            for pattern in phone_regex:
                matches = re.findall(pattern, text)
                if matches:
                    search_results["utf8_text"] = True
                    search_results["found_numbers"].extend(matches)
        except:
            pass
        
        # البحث في hex
        hex_data = data.hex()
        phone_hex_patterns = [
            '393634',  # "964"
            '373830',  # "780" 
            '393339'   # "939"
        ]
        
        for pattern in phone_hex_patterns:
            if pattern in hex_data:
                pos = hex_data.find(pattern)
                search_results["hex_patterns"].append({
                    "pattern": pattern,
                    "decoded": bytes.fromhex(pattern).decode(),
                    "position": pos // 2
                })
        
        return search_results
    
    def extract_json_data(self, data: bytes) -> Dict:
        """استخراج بيانات JSON"""
        
        json_results = {
            "found_json": False,
            "json_objects": [],
            "partial_json": [],
            "json_like_patterns": []
        }
        
        try:
            text = data.decode('utf-8', errors='ignore')
            
            # البحث عن JSON كامل
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            matches = re.findall(json_pattern, text)
            
            for match in matches:
                try:
                    parsed = json.loads(match)
                    json_results["json_objects"].append(parsed)
                    json_results["found_json"] = True
                except:
                    json_results["partial_json"].append(match)
            
            # البحث عن أنماط JSON
            if '"' in text and ':' in text:
                # استخراج key-value pairs
                kv_pattern = r'"([^"]+)"\s*:\s*"([^"]*)"'
                kv_matches = re.findall(kv_pattern, text)
                if kv_matches:
                    json_results["json_like_patterns"] = kv_matches[:10]
        
        except:
            pass
        
        return json_results
    
    def analyze_text_content(self, data: bytes) -> Dict:
        """تحليل محتوى النص"""
        
        text_analysis = {
            "readable_strings": [],
            "keywords_found": [],
            "language_hints": [],
            "structure_indicators": []
        }
        
        try:
            text = data.decode('utf-8', errors='ignore')
            
            # استخراج strings قابلة للقراءة
            readable_pattern = r'[a-zA-Z0-9\s\-_\.@]{6,}'
            readable_matches = re.findall(readable_pattern, text)
            text_analysis["readable_strings"] = readable_matches[:20]
            
            # البحث عن كلمات مفتاحية
            keywords = [
                "name", "phone", "result", "status", "data", "success",
                "اسم", "هاتف", "نتيجة", "حالة", "بيانات", "نجح"
            ]
            
            for keyword in keywords:
                if keyword in text.lower():
                    text_analysis["keywords_found"].append(keyword)
            
            # مؤشرات البنية
            if '"name"' in text or '"phone"' in text:
                text_analysis["structure_indicators"].append("contact_data")
            if '"result"' in text or '"status"' in text:
                text_analysis["structure_indicators"].append("api_response")
        
        except:
            pass
        
        return text_analysis
    
    def make_final_verdict(self, analysis: Dict) -> Dict:
        """الحكم النهائي على نجاح فك التشفير"""
        
        verdict = {
            "success_score": 0,
            "verdict": "failed",
            "confidence": 0,
            "reasons": [],
            "recommendations": []
        }
        
        score = 0
        
        # نقاط للعثور على رقم الهاتف
        if analysis["phone_search"]["raw_bytes"] or analysis["phone_search"]["utf8_text"]:
            score += 50
            verdict["reasons"].append("phone_number_found")
        
        # نقاط للـ JSON
        if analysis["json_extraction"]["found_json"]:
            score += 40
            verdict["reasons"].append("valid_json_found")
        elif analysis["json_extraction"]["partial_json"]:
            score += 20
            verdict["reasons"].append("partial_json_found")
        
        # نقاط للنص القابل للقراءة
        if analysis["text_analysis"]["keywords_found"]:
            score += len(analysis["text_analysis"]["keywords_found"]) * 5
            verdict["reasons"].append("relevant_keywords_found")
        
        # نقاط لفك الضغط الناجح
        successful_decomp = [k for k, v in analysis["decompression_attempts"].items() if v.get("success")]
        if successful_decomp:
            score += 30
            verdict["reasons"].append(f"successful_decompression_{successful_decomp[0]}")
        
        verdict["success_score"] = score
        
        if score >= 70:
            verdict["verdict"] = "success"
            verdict["confidence"] = 0.9
        elif score >= 40:
            verdict["verdict"] = "partial_success"
            verdict["confidence"] = 0.6
        else:
            verdict["verdict"] = "failed"
            verdict["confidence"] = 0.2
        
        return verdict
    
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
    
    def print_analysis_results(self, key_name: str, analysis: Dict):
        """طباعة نتائج التحليل"""
        
        print(f"📊 التحليل الخام:")
        print(f"   Entropy: {analysis['raw_analysis']['entropy']:.2f}")
        print(f"   نسبة النص: {analysis['raw_analysis']['printable_ratio']:.2%}")
        print(f"   النوع المحتمل: {analysis['raw_analysis']['suspected_format']}")
        
        print(f"\n📞 البحث عن الهاتف:")
        phone_search = analysis["phone_search"]
        if phone_search["found_numbers"]:
            print(f"   ✅ وجدنا أرقام: {phone_search['found_numbers']}")
        else:
            print(f"   ❌ لم نجد أرقام هواتف")
        
        print(f"\n🗜️ فك الضغط:")
        for method, result in analysis["decompression_attempts"].items():
            if result.get("success"):
                print(f"   ✅ {method}: نجح ({result['size']} bytes)")
                if result.get("contains_phone"):
                    print(f"      🎯 يحتوي على رقم الهاتف!")
            else:
                print(f"   ❌ {method}: فشل")
        
        print(f"\n📄 JSON:")
        json_data = analysis["json_extraction"]
        if json_data["found_json"]:
            print(f"   ✅ وجدنا {len(json_data['json_objects'])} JSON objects")
            for obj in json_data["json_objects"]:
                print(f"      📋 {json.dumps(obj, ensure_ascii=False)[:100]}...")
        else:
            print(f"   ❌ لم نجد JSON صالح")
        
        print(f"\n🏆 الحكم النهائي:")
        verdict = analysis["final_verdict"]
        print(f"   النتيجة: {verdict['verdict']}")
        print(f"   النقاط: {verdict['success_score']}")
        print(f"   الثقة: {verdict['confidence']:.1%}")
        print(f"   الأسباب: {', '.join(verdict['reasons'])}")

def main():
    """تشغيل التحليل النهائي للمفاتيح"""
    
    # ضع البيانات المشفرة هنا
    encrypted_data = "bzuuAAAy97Nim6pFd6TASAYwYeVqUj0a1ZRd+hYNg0zHBajAtZEaMuYauBarTyEM805MJWMt34mYhJ7QKflet+avUVIvaWtoZrOPW6nZzxEUcsDwab7G7bmILrcEgvku2jZwajq05l3QJu74u1rN5zF+pEdtD30Fck2RC9gGVV7ZcLeEjLvAn5SjRO3zBB/F3/kX97GuldO78/B813/fEjq6QNJ8dO8V4sxQqgCIJNVer3/EQa57MixO7rqYv6vgPB6xT5hQMacAndHHIW+bOeC2i83wT8dVKzdZjPLHnJL5SFrcUw2s8+yRW8r9UOeJq9PyikId84Cwz6pcrdCLvpwyQyFlXNNg1+YfTIvajPhkVDWaDbmU8aAfgv27XoTfYzo8K+m/D9gxehX+FLOyPD81xsGuaWtp+Z5tUhNstz91i6ddQFf0zK8VkGtolW1oU8pwGshezIVjv/fc5hwnFwDxEMQ8LEf8P00hb+DblW/RGzN2BOnyu51pa+syGvMwbLz+Dtg0Mi7AA+PpTcga7cgUob+LPgRduF1q112ZpqshA6wmfc9nexFiuKXjGOR+lB18+CEvgdVPufLfhahG+P1Eo8nFmDiuiT4MiZ/oMG7a3W012odQd1AVXIp0vdXHpSJthhG8LQkJF7ZcqJ6vs2wt5re8k+bbX2x96jO/VLDGh1oIRrIqhSnT6Ov5nwibodojDl84jR2zCRIrIMlNjlqGJMziH0+nR6njNq0ZzyGpNvtIdzJQs6xRap5MQJkf1MmitsVz6WmG2hmItCyWY4ITcXQpsRSXcZfy3kfFs9Cgx43NiK4v1voXQLMGGBbHGdWXuF1fVjwraeycb92FiNFE+BeZEKxJ9tDzYT6MkpVUJE97Qh/usql65+I9p79fFsPq2+TU695vugW1iGhogZTgYU2+JekBEH7lLOi/UggpW9ph7wE0pOAVP8+Rh4MqBHoUsEJQtVKH6YMkvTnZZe81V6ZYqNL1A6z905AhhuUU9jAUbyel9iUd29bogW7fNxcO8lwngbgxJ6LoSKzDaAuZm9Gd6qzTeylivDljSu5UCjhnpZBupIlNa2sR3GjTKvsvs8i2z50U740+vcLutTNgU43625iLt5RcZXd9cgVxvUThazDQl4zShVXi5hXAxIxQJDpV13N1yTmq8UtDJH//9MM7tnVdNOLl3gjX1DfulL6lYhs83Vf5KZv1ccVPVN4PLMq5yVPIV4WCU6lIbD/rfB4IwZCgge/IX2WJhbG/QYfhjD7oJfcKbCm0iccof2bDSpi0daCO4KnnxxuahX5zyLiRgBFqSCFnXI6hB7/mjItEXXGFDDwV/j4j+BmFjX2vXrECE2hrgy/dtntG9Jc9RPQ12PXjikxXOBgNpUdQcq8Ko+Xhn5XkN3XeKLULY4U4hUboYiylv9xP1mR2CkyvgbolUntxqvwIDZLdMtgLKBVRsE+jOSHESTGVcy2TdsjNx9flCBSLghe9UacDL8AXKmKVs5bCJRyC5lnS/jj3ROUI3G+87kRLMg0LsPq6QUxmFLft2b6GI5MNBoGR25+GwSuX7ZQzbWxG+n94gUFri2jd/SWgH/n2IWQP++74BMTse76mnL2ze+7wUf2PPxDvAm2Xxg2SXDVukjHyrvXOdfzObMo61NiHHxDgU0mr83naa9jz60lFHF2y21C1BgeUvbjwleSR+ECgiJrHuhdiTp16DD4dhhKR0tB0Badyw1BLuqKYl6i52kKXcaiNApVUU7wflRc8P6IyYd0v7ZfNwPx9oxpEXNWt83BgM4cRHsKtT4nTPyq/OpUGCDPRTUpYjTCJH+JEjMbmznR72SnPxx5zV+8bNR6ALUEB3XAKRQ29rR+BSDc3j8JdvKkI3Jg2stNsl5pMrvAhTStIoxZiD5Afi7a2kacgtuULeXH6vPp5VDPsBACMLvVRaoI5yRKqY7XhqkJb1pIgBoaNez+knKpK/ieij6lH8RrwgzDAtmw/wNnIaATZLaLhwFZRMkozROkCiN3VJmqQF1msnVE/2wCg5+ekGtzidRPQCfwJVVugXuql8r6aB5B96HcfXEHQTyeSR7YEIbmhSu/d/O2aJssVGlJyQU+b+aPujrxOvb/NPKMBHDG3FieIwpVeN9VLuibYPMivIFlnXm8KDTEpH3r0FxmIYMhebOj8ehTa+dbrtU0Z0t3MrJRBEFYmEsf23JYP8P71t1K80+7dhsP++L2ATiG0LIG18eyEfj1wdfkx3JEet4u4sP/vUQYuHt5X0lKgahPg2Gu1EH8xOuIaP2TjHM2MnnGurniHP+YqcKPWx7lDjIFcA9nk/mQcMRu7OhynyDV8oIoqn9rQvrlRBsJ5oFiQcIS1KExJW1d4KXaKaKufMxVCPn065QJGNKf2t7liDplmDHXynlEba2AC/epdh72fJyjLlBPKXNlVodWh40pnzNpZ50jSVYrXttBYkiYIh0XP+M5vJx54dPNSIyXOxp+DLGc7lV6M8ILRor/KxIq/2r3sAqie8Xj7w4443nCitmGOldrLb0PGoeg/pbzW28T0HqpHDORYfqjmCx+ErPZH01wSWavBGyIjpfCo8S/eTzdPbupjFCN3QXiBWImOqnjl4bPqWmTXzu//KEqNPh+66tIUhTuY7fS6WIcZGlvCL0wgXN8OytZPffihoKAxZ/lprfwmaMfl1ms3vcnht7Z8Luo7Ky5eeBIH7WTxPyldf3qRLOI3hrP/OO6MQjffaUyuEK2pmoplfVeQiDP50Ef94ydNix/9Bb7vmr7sZn2vIw9buiyIHwg/cak/tLCFtmsIrmTjhiMy2NN7hzx0aHTUAI4TyN9W/56lJWz09gwvcg1xfUZptBi3ctWVSsoLgepBdQw2Mxn1Vr9WCEICBzCyeXEfoFbT1WSd9ZilkXgBHVnk3wYchb7tt3oGMVxc8daEIaSnxmaB7NqLsJVAJrs4RKz60X1mGCfdoXa9CZVZKu0s9SAHuGZkYWb+S2VUqGTJu1B0FKguxOaeE8V5xl3NJVekw5P5OWEzOZdRuTvVFkEgmN+LCk3ouHYCeZyptNM9jBYGp5tp8nmDAR37HYfhMVGjDjCWFLn7xyFs/6IqdiZnfEBpK3whKnJOKJKedE3k6avC6T4HN4ujhKsQJtsHH/eOsSSRTiv4CBxXWUmUVuv5pDFEniqs5mcHNaaPYyvHMJxHZc9M5u0IMd62fR1LnZQGnswmncBRUiX08SeGVmC6ItOhdNuMfUFKtkmK0TPeRfMwMBDFO1D0bJPGi5rEy2RYK+8A5Ue0EzI/wXqWKjstTZjk/kHNON/NG71bo+fpn6CNs9V6tJQ+ufi7Sgj//Zxwyb/tW3zdxU6kRGL2L1mWRWmwDYo77OUawjR6J5W1Ovkf3zLfpDjfSqu1vTzf1fEWzKxdzwtlO4ennMr00Fz+43D2N1JXXVpxMibO7ty+cPksGfAaQtwz1SetUHC15Cqxvl1sOdC4A9fSvNNa+4dJ2fkMtclElkF8BkglDEt69VlveAfIjUyh5bdhQkqKLKf1+5MjFw2jHt6DShDSmp+ZiCCn69XpJpt5UwOUiYg6X5+QfZDd+G0fSO8GXdeRheUlZrxT7MKV4iIw9m+srfIZTQyaTq4eIlLVjAMWj1sKVNrPJoB+M3CQDv+ndT0s+IG6CgAWFicV8eB6k80Eh+YZ914xP6A0nYvgBozM38FafUUAj7j65PsFgPMnnd3XMn76JfceALOheVEMcOFfSMFQeEwT0UfqXtA+XJkhD4aGUdYjsJw9XKl8JchZl0jIaLq5/qoUiJIGY/y+aacbKsmx0PtvdVbh6QnwMka3D/pDxfQf8lGhbG0aSfWC9D9DCRASPwk/aMW4BWebBHnU63QdqezV/r8V8TrO2pg9zjx0O8+347y0dXuAjMSTunQD0QBioOCq+lhUjRdT++7ssN/dHNEXR5AAvkgq6zMlw7UcTPhUJMnyMuaYKTGgZo8gyqkrf2eW23CcvKsKNHTeW1Kju1YmrBcp2M0jT2dv7Wivhn+4HzNeuMc9PmCRgWxbr5fyvqtWRyvzkEp3G+Uj9fsXuK8Q6IaMZUEWk67WyREkm0jYiMP3FjUdTWtOazIO3fgomedkJT1EmeAVV70y9sILKDlIA5SPK6g2MfCAZASujijaimixvJLIF/+O07PCngZjEwRY/tIOhWRGphQS5mwnYS1JGkK/XdnfbnncVQUcsEZKe3PZ2NSJ/t0JzQxqVlGAK30PoMbMB1HTyc6UQ5XsHqiuWqrdHC9L0FZSWIrH1DiSHSilmvgrONqkzjPB7TLlx9ihb3mueVyPxaVkliAl47LAgrv8HRwv9gpqBU4syUkNW8dC6Rg7gRn2BCtaEt3SqWQpBGrKW2UVOdX89NllvvMb410A2PiCwtSL4rF14UxoDjnkLNrhmR36ETcp1XVYofS0qcJPSV1Y6YZqEJ6hyrLgyTm83YV/29c3Kjh3yCS0BWd1GdTo3Ynz95QbIP1BuQUmTJ6Le74M8LUTRNniWIANW4VE7ZyZ5Jv4fr6DkTNMuNRKTgy+vhEn1gasR3h40nlXxMdRL5f4jlwL+/Xn16MPpjJpfUdnrC6tqDSJaqNc1AlqLYVcZe3JcXxlpiNtNFu0ABQE4o+krs4sjK7q7d4q3v9SY8Z1W1P+obgwldOoK9R2db1+0SfXgpYjB0TArXcgDir8iRtcnjBU6bCSZDUaV80jJZW1m2wLcJzexh89V64d3BzY+6OguCcekwmg61hDx16ohwb91J2JgMFeqke8M/zOheTh3TSGUWodAnCmzDT/jFNoR6eh+j3fvLZdlvKI6aH1Vg2JK6NlQ5rKaIOMk8dXWsmhs9kU+OcSJmRlDDWgnaiHBTTKECQdVvS2t7I2+AnrUrIX2HLCw0QxGPvfhJOBb56mGkwEcra/j84evyw1lHVDO/ppe2Ad6KXbbo0pau4Sj7EzKJ+DI7C382QF80qQY6reKBwxrLgPiZsM3sKcYLKWoNTTXVYLfyAgHzy2J7Fg1VKMKXe/U4g31h2RZ+IDtOdk7tdeiN6rP6SCpS4khwt6IIwrh0AgtPBGwqkGcfpm3Kzmal5fk2QveR1hdwVSktPA6BM4NYVtY8MuUXOXLP5ogo9xOZyCA63AqLgeu2WKr62Wv7iPScIXiIGirEzHBLSPObDtVc44bXcqZNrqjPcUOlnSBqL/ZbHoLLhmpMnNXhmkxBl+7uh5xFYNJbwetxt+zLyyGgGNdD0kG4bZGIkSyNeKmXuOSh4=="
    
    if encrypted_data == "[ENCRYPTED_DATA_PLACEHOLDER]":
        print("⚠️ ضع البيانات المشفرة في encrypted_data")
        return
    
    analyzer = FinalKeyAnalysis()
    
    print("🎯 بدء التحليل النهائي للمفاتيح الواعدة...")
    print("=" * 70)
    
    results = analyzer.deep_analysis_of_keys(encrypted_data)
    
    print("\n" + "=" * 70)
    print("🏆 الملخص النهائي:")
    
    best_result = None
    best_score = 0
    
    for key_name, result in results.items():
        score = result["analysis"]["final_verdict"]["success_score"]
        verdict = result["analysis"]["final_verdict"]["verdict"]
        
        print(f"\n🔑 {key_name}:")
        print(f"   📊 النقاط: {score}")
        print(f"   📈 النتيجة: {verdict}")
        
        if score > best_score:
            best_score = score
            best_result = (key_name, result)
    
    if best_result and best_score >= 40:
        print(f"\n🥇 أفضل نتيجة: {best_result[0]} ({best_score} نقطة)")
        
        # إذا كان لدينا نجاح، اطبع البيانات المفكوكة
        if best_score >= 70:
            print("🎉 تم فك التشفير بنجاح!")
            # يمكن إضافة طباعة البيانات الكاملة هنا
    else:
        print("\n😔 لم نحقق نجاح كامل - قد نحتاج مقاربة أخرى")
    
    return results

if __name__ == "__main__":
    main()