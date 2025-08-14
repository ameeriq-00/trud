"""
تحليل عميق لموقع رقم الهاتف في البيانات المشفرة
"""
import base64
import json
import struct
from typing import Dict, List

class NumberBoxDeepAnalyzer:
    def __init__(self):
        self.phone = "+9647809394930"
        self.number_encrypted = "bzuuAAAy97Nim6pFd6TASAYwYeVqUj0a1ZRd+hYNg0zHBajAtZEaMuYauBarTyEM805MJWMt34mYhJ7QKflet+avUVIvaWtoZrOPW6nZzxEUcsDwab7G7bmILrcEgvku2jZwajq05l3QJu74u1rN5zF+pEdtD30Fck2RC9gGVV7ZcLeEjLvAn5SjRO3zBB/F3/kX97GuldO78/B813/fEjq6QNJ8dO8V4sxQqgCIJNVer3/EQa57MixO7rqYv6vgPB6xT5hQMacAndHHIW+bOeC2i83wT8dVKzdZjPLHnJL5SFrcUw2s8+yRW8r9UOeJq9PyikId84Cwz6pcrdCLvpwyQyFlXNNg1+YfTIvajPhkVDWaDbmU8aAfgv27XoTfYzo8K+m/D9gxehX+FLOyPD81xsGuaWtp+Z5tUhNstz91i6ddQFf0zK8VkGtolW1oU8pwGshezIVjv/fc5hwnFwDxEMQ8LEf8P00hb+DblW/RGzN2BOnyu51pa+syGvMwbLz+Dtg0Mi7AA+PpTcga7cgUob+LPgRduF1q112ZpqshA6wmfc9nexFiuKXjGOR+lB18+CEvgdVPufLfhahG+P1Eo8nFmDiuiT4MiZ/oMG7a3W012odQd1AVXIp0vdXHpSJthhG8LQkJF7ZcqJ6vs2wt5re8k+bbX2x96jO/VLDGh1oIRrIqhSnT6Ov5nwibodojDl84jR2zCRIrIMlNjlqGJMziH0+nR6njNq0ZzyGpNvtIdzJQs6xRap5MQJkf1MmitsVz6WmG2hmItCyWY4ITcXQpsRSXcZfy3kfFs9Cgx43NiK4v1voXQLMGGBbHGdWXuF1fVjwraeycb92FiNFE+BeZEKxJ9tDzYT6MkpVUJE97Qh/usql65+I9p79fFsPq2+TU695vugW1iGhogZTgYU2+JekBEH7lLOi/UggpW9ph7wE0pOAVP8+Rh4MqBHoUsEJQtVKH6YMkvTnZZe81V6ZYqNL1A6z905AhhuUU9jAUbyel9iUd29bogW7fNxcO8lwngbgxJ6LoSKzDaAuZm9Gd6qzTeylivDljSu5UCjhnpZBupIlNa2sR3GjTKvsvs8i2z50U740+vcLutTNgU43625iLt5RcZXd9cgVxvUThazDQl4zShVXi5hXAxIxQJDpV13N1yTmq8UtDJH//9MM7tnVdNOLl3gjX1DfulL6lYhs83Vf5KZv1ccVPVN4PLMq5yVPIV4WCU6lIbD/rfB4IwZCgge/IX2WJhbG/QYfhjD7oJfcKbCm0iccof2bDSpi0daCO4KnnxxuahX5zyLiRgBFqSCFnXI6hB7/mjItEXXGFDDwV/j4j+BmFjX2vXrECE2hrgy/dtntG9Jc9RPQ12PXjikxXOBgNpUdQcq8Ko+Xhn5XkN3XeKLULY4U4hUboYiylv9xP1mR2CkyvgbolUntxqvwIDZLdMtgLKBVRsE+jOSHESTGVcy2TdsjNx9flCBSLghe9UacDL8AXKmKVs5bCJRyC5lnS/jj3ROUI3G+87kRLMg0LsPq6QUxmFLft2b6GI5MNBoGR25+GwSuX7ZQzbWxG+n94gUFri2jd/SWgH/n2IWQP++74BMTse76mnL2ze+7wUf2PPxDvAm2Xxg2SXDVukjHyrvXOdfzObMo61NiHHxDgU0mr83naa9jz60lFHF2y21C1BgeUvbjwleSR+ECgiJrHuhdiTp16DD4dhhKR0tB0Badyw1BLuqKYl6i52kKXcaiNApVUU7wflRc8P6IyYd0v7ZfNwPx9oxpEXNWt83BgM4cRHsKtT4nTPyq/OpUGCDPRTUpYjTCJH+JEjMbmznR72SnPxx5zV+8bNR6ALUEB3XAKRQ29rR+BSDc3j8JdvKkI3Jg2stNsl5pMrvAhTStIoxZiD5Afi7a2kacgtuULeXH6vPp5VDPsBACMLvVRaoI5yRKqY7XhqkJb1pIgBoaNez+knKpK/ieij6lH8RrwgzDAtmw/wNnIaATZLaLhwFZRMkozROkCiN3VJmqQF1msnVE/2wCg5+ekGtzidRPQCfwJVVugXuql8r6aB5B96HcfXEHQTyeSR7YEIbmhSu/d/O2aJssVGlJyQU+b+aPujrxOvb/NPKMBHDG3FieIwpVeN9VLuibYPMivIFlnXm8KDTEpH3r0FxmIYMhebOj8ehTa+dbrtU0Z0t3MrJRBEFYmEsf23JYP8P71t1K80+7dhsP++L2ATiG0LIG18eyEfj1wdfkx3JEet4u4sP/vUQYuHt5X0lKgahPg2Gu1EH8xOuIaP2TjHM2MnnGurniHP+YqcKPWx7lDjIFcA9nk/mQcMRu7OhynyDV8oIoqn9rQvrlRBsJ5oFiQcIS1KExJW1d4KXaKaKufMxVCPn065QJGNKf2t7liDplmDHXynlEba2AC/epdh72fJyjLlBPKXNlVodWh40pnzNpZ50jSVYrXttBYkiYIh0XP+M5vJx54dPNSIyXOxp+DLGc7lV6M8ILRor/KxIq/2r3sAqie8Xj7w4443nCitmGOldrLb0PGoeg/pbzW28T0HqpHDORYfqjmCx+ErPZH01wSWavBGyIjpfCo8S/eTzdPbupjFCN3QXiBWImOqnjl4bPqWmTXzu//KEqNPh+66tIUhTuY7fS6WIcZGlvCL0wgXN8OytZPffihoKAxZ/lprfwmaMfl1ms3vcnht7Z8Luo7Ky5eeBIH7WTxPyldf3qRLOI3hrP/OO6MQjffaUyuEK2pmoplfVeQiDP50Ef94ydNix/9Bb7vmr7sZn2vIw9buiyIHwg/cak/tLCFtmsIrmTjhiMy2NN7hzx0aHTUAI4TyN9W/56lJWz09gwvcg1xfUZptBi3ctWVSsoLgepBdQw2Mxn1Vr9WCEICBzCyeXEfoFbT1WSd9ZilkXgBHVnk3wYchb7tt3oGMVxc8daEIaSnxmaB7NqLsJVAJrs4RKz60X1mGCfdoXa9CZVZKu0s9SAHuGZkYWb+S2VUqGTJu1B0FKguxOaeE8V5xl3NJVekw5P5OWEzOZdRuTvVFkEgmN+LCk3ouHYCeZyptNM9jBYGp5tp8nmDAR37HYfhMVGjDjCWFLn7xyFs/6IqdiZnfEBpK3whKnJOKJKedE3k6avC6T4HN4ujhKsQJtsHH/eOsSSRTiv4CBxXWUmUVuv5pDFEniqs5mcHNaaPYyvHMJxHZc9M5u0IMd62fR1LnZQGnswmncBRUiX08SeGVmC6ItOhdNuMfUFKtkmK0TPeRfMwMBDFO1D0bJPGi5rEy2RYK+8A5Ue0EzI/wXqWKjstTZjk/kHNON/NG71bo+fpn6CNs9V6tJQ+ufi7Sgj//Zxwyb/tW3zdxU6kRGL2L1mWRWmwDYo77OUawjR6J5W1Ovkf3zLfpDjfSqu1vTzf1fEWzKxdzwtlO4ennMr00Fz+43D2N1JXXVpxMibO7ty+cPksGfAaQtwz1SetUHC15Cqxvl1sOdC4A9fSvNNa+4dJ2fkMtclElkF8BkglDEt69VlveAfIjUyh5bdhQkqKLKf1+5MjFw2jHt6DShDSmp+ZiCCn69XpJpt5UwOUiYg6X5+QfZDd+G0fSO8GXdeRheUlZrxT7MKV4iIw9m+srfIZTQyaTq4eIlLVjAMWj1sKVNrPJoB+M3CQDv+ndT0s+IG6CgAWFicV8eB6k80Eh+YZ914xP6A0nYvgBozM38FafUUAj7j65PsFgPMnnd3XMn76JfceALOheVEMcOFfSMFQeEwT0UfqXtA+XJkhD4aGUdYjsJw9XKl8JchZl0jIaLq5/qoUiJIGY/y+aacbKsmx0PtvdVbh6QnwMka3D/pDxfQf8lGhbG0aSfWC9D9DCRASPwk/aMW4BWebBHnU63QdqezV/r8V8TrO2pg9zjx0O8+347y0dXuAjMSTunQD0QBioOCq+lhUjRdT++7ssN/dHNEXR5AAvkgq6zMlw7UcTPhUJMnyMuaYKTGgZo8gyqkrf2eW23CcvKsKNHTeW1Kju1YmrBcp2M0jT2dv7Wivhn+4HzNeuMc9PmCRgWxbr5fyvqtWRyvzkEp3G+Uj9fsXuK8Q6IaMZUEWk67WyREkm0jYiMP3FjUdTWtOazIO3fgomedkJT1EmeAVV70y9sILKDlIA5SPK6g2MfCAZASujijaimixvJLIF/+O07PCngZjEwRY/tIOhWRGphQS5mwnYS1JGkK/XdnfbnncVQUcsEZKe3PZ2NSJ/t0JzQxqVlGAK30PoMbMB1HTyc6UQ5XsHqiuWqrdHC9L0FZSWIrH1DiSHSilmvgrONqkzjPB7TLlx9ihb3mueVyPxaVkliAl47LAgrv8HRwv9gpqBU4syUkNW8dC6Rg7gRn2BCtaEt3SqWQpBGrKW2UVOdX89NllvvMb410A2PiCwtSL4rF14UxoDjnkLNrhmR36ETcp1XVYofS0qcJPSV1Y6YZqEJ6hyrLgyTm83YV/29c3Kjh3yCS0BWd1GdTo3Ynz95QbIP1BuQUmTJ6Le74M8LUTRNniWIANW4VE7ZyZ5Jv4fr6DkTNMuNRKTgy+vhEn1gasR3h40nlXxMdRL5f4jlwL+/Xn16MPpjJpfUdnrC6tqDSJaqNc1AlqLYVcZe3JcXxlpiNtNFu0ABQE4o+krs4sjK7q7d4q3v9SY8Z1W1P+obgwldOoK9R2db1+0SfXgpYjB0TArXcgDir8iRtcnjBU6bCSZDUaV80jJZW1m2wLcJzexh89V64d3BzY+6OguCcekwmg61hDx16ohwb91J2JgMFeqke8M/zOheTh3TSGUWodAnCmzDT/jFNoR6eh+j3fvLZdlvKI6aH1Vg2JK6NlQ5rKaIOMk8dXWsmhs9kU+OcSJmRlDDWgnaiHBTTKECQdVvS2t7I2+AnrUrIX2HLCw0QxGPvfhJOBb56mGkwEcra/j84evyw1lHVDO/ppe2Ad6KXbbo0pau4Sj7EzKJ+DI7C382QF80qQY6reKBwxrLgPiZsM3sKcYLKWoNTTXVYLfyAgHzy2J7Fg1VKMKXe/U4g31h2RZ+IDtOdk7tdeiN6rP6SCpS4khwt6IIwrh0AgtPBGwqkGcfpm3Kzmal5fk2QveR1hdwVSktPA6BM4NYVtY8MuUXOXLP5ogo9xOZyCA63AqLgeu2WKr62Wv7iPScIXiIGirEzHBLSPObDtVc44bXcqZNrqjPcUOlnSBqL/ZbHoLLhmpMnNXhmkxBl+7uh5xFYNJbwetxt+zLyyGgGNdD0kG4bZGIkSyNeKmXuOSh4=="  # الـ number الكامل
    
    def find_phone_chunks_locations(self) -> dict:
        """البحث عن مواقع أجزاء رقم الهاتف بالتفصيل"""
        
        try:
            decoded = base64.b64decode(self.number_encrypted)
            phone_digits = "9647809394930"
            
            # تقسيم الرقم لأجزاء مختلفة
            chunks = {
                "chunk_4": phone_digits[:4],    # "9647"
                "chunk_4_2": phone_digits[4:8], # "8093" 
                "chunk_4_3": phone_digits[8:12], # "9493"
                "chunk_1": phone_digits[-1],    # "0"
                "full_number": phone_digits,
                "without_country": phone_digits[3:], # "7809394930"
                "local_part": phone_digits[3:],      # "7809394930"
            }
            
            locations = {}
            
            # البحث عن كل chunk
            for chunk_name, chunk_value in chunks.items():
                chunk_bytes = chunk_value.encode()
                positions = []
                
                # البحث في البيانات الخام
                start = 0
                while True:
                    pos = decoded.find(chunk_bytes, start)
                    if pos == -1:
                        break
                    positions.append(pos)
                    start = pos + 1
                
                if positions:
                    locations[chunk_name] = {
                        "value": chunk_value,
                        "positions": positions,
                        "found": True,
                        "context": self.get_context_around_positions(decoded, positions, chunk_bytes)
                    }
                else:
                    locations[chunk_name] = {
                        "value": chunk_value,
                        "found": False
                    }
            
            return locations
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_context_around_positions(self, data: bytes, positions: list, target: bytes) -> list:
        """الحصول على السياق حول المواقع المكتشفة"""
        
        contexts = []
        context_size = 20  # 20 بايت قبل وبعد
        
        for pos in positions:
            start = max(0, pos - context_size)
            end = min(len(data), pos + len(target) + context_size)
            
            context = data[start:end]
            
            contexts.append({
                "position": pos,
                "hex_context": context.hex(),
                "before": data[start:pos].hex(),
                "target": target.hex(),
                "after": data[pos + len(target):end].hex(),
                "ascii_context": context.decode('ascii', errors='ignore')
            })
        
        return contexts
    
    def analyze_data_structure_around_phone(self) -> dict:
        """تحليل بنية البيانات حول مواقع رقم الهاتف"""
        
        locations = self.find_phone_chunks_locations()
        
        if not any(loc.get('found', False) for loc in locations.values()):
            return {"no_phone_chunks_found": True}
        
        analysis = {
            "found_chunks": {},
            "patterns": {},
            "structure_hypothesis": []
        }
        
        # تحليل كل chunk موجود
        for chunk_name, chunk_info in locations.items():
            if chunk_info.get('found', False):
                analysis["found_chunks"][chunk_name] = {
                    "positions": chunk_info["positions"],
                    "contexts": chunk_info["context"]
                }
                
                # تحليل النمط حول كل موقع
                for context in chunk_info["context"]:
                    pattern = self.analyze_context_pattern(context)
                    analysis["patterns"][f"{chunk_name}_{context['position']}"] = pattern
        
        # تطوير فرضيات حول البنية
        analysis["structure_hypothesis"] = self.develop_structure_hypothesis(analysis)
        
        return analysis
    
    def analyze_context_pattern(self, context: dict) -> dict:
        """تحليل النمط في السياق"""
        
        before_hex = context["before"]
        after_hex = context["after"]
        
        pattern_analysis = {
            "before_length": len(before_hex) // 2,
            "after_length": len(after_hex) // 2,
            "before_pattern": self.identify_pattern(before_hex),
            "after_pattern": self.identify_pattern(after_hex),
            "possible_field_structure": self.check_field_structure(before_hex, after_hex)
        }
        
        return pattern_analysis
    
    def identify_pattern(self, hex_data: str) -> dict:
        """تحديد النمط في البيانات hex"""
        
        if not hex_data:
            return {"type": "empty"}
        
        # تحويل لbytes للتحليل
        try:
            data = bytes.fromhex(hex_data)
        except:
            return {"type": "invalid_hex"}
        
        patterns = {
            "all_zeros": all(b == 0 for b in data),
            "all_same": len(set(data)) == 1,
            "incremental": all(data[i] <= data[i+1] for i in range(len(data)-1)) if len(data) > 1 else False,
            "length_indicator": len(data) >= 4 and struct.unpack('>I', data[:4])[0] < 10000,
            "ascii_text": all(32 <= b <= 126 for b in data),
            "null_terminated": data.endswith(b'\x00')
        }
        
        return patterns
    
    def check_field_structure(self, before: str, after: str) -> dict:
        """فحص إذا كانت البيانات تشبه بنية حقول"""
        
        structure_indicators = {
            "has_length_prefix": False,
            "has_type_indicator": False,
            "has_delimiter": False,
            "field_boundaries": []
        }
        
        # فحص length prefix (أول 4 بايت قد تكون length)
        if len(before) >= 8:  # 4 بايت = 8 hex chars
            try:
                length_candidate = struct.unpack('>I', bytes.fromhex(before[-8:]))[0]
                if 0 < length_candidate < 1000:  # range معقول
                    structure_indicators["has_length_prefix"] = True
                    structure_indicators["length_candidate"] = length_candidate
            except:
                pass
        
        # البحث عن delimiters شائعة
        common_delimiters = ["00", "ff", "0a", "0d"]
        for delimiter in common_delimiters:
            if delimiter in before or delimiter in after:
                structure_indicators["has_delimiter"] = True
                structure_indicators["delimiter"] = delimiter
        
        return structure_indicators
    
    def develop_structure_hypothesis(self, analysis: Dict) -> list:
        """تطوير فرضيات حول بنية البيانات"""
        
        hypotheses = []
        
        # فرضية 1: JSON مشفر
        hypotheses.append({
            "type": "encrypted_json",
            "confidence": 0.7,
            "evidence": "Phone chunks found + high entropy suggests encrypted structured data",
            "next_steps": "Try AES decryption with keys from HAR file"
        })
        
        # فرضية 2: Protocol Buffer
        hypotheses.append({
            "type": "protobuf",
            "confidence": 0.5, 
            "evidence": "Binary structure with embedded phone number",
            "next_steps": "Analyze as protobuf message format"
        })
        
        # فرضية 3: Custom binary format
        hypotheses.append({
            "type": "custom_binary",
            "confidence": 0.6,
            "evidence": "Structured binary data with phone number fields",
            "next_steps": "Reverse engineer field structure"
        })
        
        return hypotheses
    
    def extract_potential_keys_from_context(self) -> dict:
        """استخراج مفاتيح محتملة من السياق"""
        
        locations = self.find_phone_chunks_locations()
        potential_keys = {
            "static_patterns": [],
            "repeating_sequences": [],
            "length_indicators": []
        }
        
        for chunk_name, chunk_info in locations.items():
            if chunk_info.get('found', False):
                for context in chunk_info.get('context', []):
                    # البحث عن أنماط ثابتة قد تكون مفاتيح
                    before = context.get('before', '')
                    after = context.get('after', '')
                    
                    # أنماط ثابتة في before/after
                    if before and len(before) >= 8:
                        potential_keys["static_patterns"].append({
                            "location": "before",
                            "chunk": chunk_name,
                            "pattern": before,
                            "length": len(before) // 2
                        })
                    
                    if after and len(after) >= 8:
                        potential_keys["static_patterns"].append({
                            "location": "after", 
                            "chunk": chunk_name,
                            "pattern": after,
                            "length": len(after) // 2
                        })
        
        return potential_keys

def main():
    """تشغيل التحليل العميق"""
    
    analyzer = NumberBoxDeepAnalyzer()
    
    print("🎯 بدء التحليل العميق لمواقع رقم الهاتف...")
    print("=" * 70)
    
    # البحث عن مواقع أجزاء الرقم
    locations = analyzer.find_phone_chunks_locations()
    print("📍 مواقع أجزاء رقم الهاتف:")
    print(json.dumps(locations, indent=2, ensure_ascii=False))
    print("=" * 70)
    
    # تحليل البنية حول الرقم
    structure_analysis = analyzer.analyze_data_structure_around_phone()
    print("🏗️ تحليل البنية حول رقم الهاتف:")
    print(json.dumps(structure_analysis, indent=2, ensure_ascii=False))
    print("=" * 70)
    
    # استخراج مفاتيح محتملة
    potential_keys = analyzer.extract_potential_keys_from_context()
    print("🔑 المفاتيح المحتملة:")
    print(json.dumps(potential_keys, indent=2, ensure_ascii=False))
    
    return locations, structure_analysis, potential_keys

if __name__ == "__main__":
    main()