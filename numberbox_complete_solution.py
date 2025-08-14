#!/usr/bin/env python3
"""
🔥 Complete Advanced NumberBox Key Derivation & Brute Force
Continuation of the comprehensive solution
"""

import hashlib
import zipfile
import base64
import os
import struct
import binascii
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from cryptography import x509
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class AdvancedNumberBoxCrypto:
    def __init__(self, apk_path=None):
        # Known constants from IDA analysis
        self.STATIC_IV = bytes.fromhex("0F0E0D0C0B0A09080706050403020100")
        self.STATIC_DATA2 = bytes.fromhex("10000000100000001000000010")
        
        # Known test cases
        self.TEST_CASES = [
            ("+964", "zn92OT0dWHbvH2UTB01naJHL6aqsusUleB"),
            ("7809394930", "7K1MaGp9+EXKitK2U/8n4DDjbe/96r0aSK")
        ]
        
        self.certificate = None
        self.key_candidates = []
        
        if apk_path and os.path.exists(apk_path):
            self.certificate = self.extract_certificate(apk_path)
            
        print(f"🔒 Static IV: {self.STATIC_IV.hex()}")
        print(f"🔒 Static Data: {self.STATIC_DATA2.hex()}")

    def extract_certificate(self, apk_path):
        """Enhanced certificate extraction with proper parsing"""
        try:
            with zipfile.ZipFile(apk_path, 'r') as apk:
                cert_files = [f for f in apk.namelist() 
                             if 'META-INF' in f and (f.endswith('.RSA') or f.endswith('.DSA'))]
                
                if cert_files:
                    cert_data = apk.read(cert_files[0])
                    print(f"✅ Certificate: {len(cert_data)} bytes")
                    
                    # Parse PKCS#7 structure to extract the actual certificate
                    try:
                        actual_cert = self.extract_x509_from_pkcs7(cert_data)
                        if actual_cert:
                            print(f"📜 X.509 Certificate extracted: {len(actual_cert)} bytes")
                            return actual_cert
                    except Exception as e:
                        print(f"⚠️ PKCS#7 parsing failed: {e}")
                    
                    return cert_data
                else:
                    print("❌ No certificate found")
                    return None
        except Exception as e:
            print(f"❌ Certificate extraction error: {e}")
            return None

    def extract_x509_from_pkcs7(self, pkcs7_data):
        """Extract X.509 certificate from PKCS#7 container"""
        try:
            # Look for X.509 certificate start pattern
            for i in range(len(pkcs7_data) - 4):
                if pkcs7_data[i:i+2] == b'\x30\x82':
                    length_bytes = pkcs7_data[i+2:i+4]
                    cert_length = struct.unpack('>H', length_bytes)[0] + 4
                    
                    if i + cert_length <= len(pkcs7_data):
                        candidate_cert = pkcs7_data[i:i+cert_length]
                        
                        try:
                            x509.load_der_x509_certificate(candidate_cert)
                            return candidate_cert
                        except:
                            continue
            
            return None
        except Exception as e:
            print(f"❌ X.509 extraction error: {e}")
            return None

    def test_key_comprehensive(self, key, key_name):
        """Comprehensive testing of a key with different configurations"""
        
        results = []
        
        # Different IV candidates
        iv_candidates = [
            ("Static_IV", self.STATIC_IV),
            ("Zero_IV", b'\x00' * 16),
            ("Key_as_IV", key),
            ("Reversed_IV", self.STATIC_IV[::-1]),
            ("Modified_IV", bytes((b + 1) % 256 for b in self.STATIC_IV)),
        ]
        
        # Different padding strategies
        padding_methods = [
            ("PKCS7", lambda data: pad(data, 16)),
            ("Zero_Pad", lambda data: data + b'\x00' * (16 - len(data) % 16) if len(data) % 16 != 0 else data),
            ("Custom_Pad", lambda data: data + bytes([16 - len(data) % 16] * (16 - len(data) % 16)) if len(data) % 16 != 0 else data + b'\x10' * 16),
            ("No_Pad", lambda data: data if len(data) % 16 == 0 else data + b'\x00' * (16 - len(data) % 16)),
        ]
        
        for iv_name, iv in iv_candidates:
            for pad_name, pad_func in padding_methods:
                for plaintext, expected_b64 in self.TEST_CASES:
                    try:
                        plaintext_bytes = plaintext.encode('utf-8')
                        padded_data = pad_func(plaintext_bytes)
                        
                        cipher = AES.new(key, AES.MODE_CBC, iv)
                        encrypted = cipher.encrypt(padded_data)
                        result_b64 = base64.b64encode(encrypted).decode('ascii')
                        
                        # Check if it matches expected output
                        if result_b64 == expected_b64:
                            print(f"🎉 PERFECT MATCH FOUND!")
                            print(f"   Key: {key_name}")
                            print(f"   Key Hex: {key.hex()}")
                            print(f"   IV: {iv_name}")
                            print(f"   Padding: {pad_name}")
                            print(f"   Plaintext: {plaintext}")
                            print(f"   Result: {result_b64}")
                            
                            return {
                                'key_name': key_name,
                                'key_hex': key.hex(),
                                'iv_method': iv_name,
                                'iv_hex': iv.hex(),
                                'padding': pad_name,
                                'plaintext': plaintext,
                                'result': result_b64,
                                'match': True
                            }
                        
                        # Check for partial matches (first N characters)
                        for check_len in [10, 15, 20, 25]:
                            if result_b64[:check_len] == expected_b64[:check_len]:
                                print(f"⚡ Partial match ({check_len} chars): {key_name} | {iv_name} | {pad_name}")
                                results.append({
                                    'key_name': key_name,
                                    'key_hex': key.hex(),
                                    'iv_method': iv_name,
                                    'padding': pad_name,
                                    'plaintext': plaintext,
                                    'result': result_b64,
                                    'partial_match': check_len
                                })
                        
                    except Exception as e:
                        continue
        
        return results

    def generate_advanced_key_candidates(self):
        """Generate comprehensive key candidates"""
        if not self.certificate:
            print("❌ No certificate available")
            return []
        
        candidates = []
        cert_data = self.certificate
        
        print(f"🔍 Analyzing certificate ({len(cert_data)} bytes)...")
        
        # 1. Hash-based keys
        hash_functions = {
            'MD5': lambda data: hashlib.md5(data).digest()[:16],
            'SHA1': lambda data: hashlib.sha1(data).digest()[:16],
            'SHA256': lambda data: hashlib.sha256(data).digest()[:16],
            'SHA512': lambda data: hashlib.sha512(data).digest()[:16],
        }
        
        for name, hash_func in hash_functions.items():
            key = hash_func(cert_data)
            candidates.append((f"Cert_{name}", key))
        
        # 2. Certificate structure analysis
        try:
            cert_obj = x509.load_der_x509_certificate(cert_data)
            
            # Subject/Issuer based
            subject_der = cert_obj.subject.public_bytes()
            issuer_der = cert_obj.issuer.public_bytes()
            
            for entity_name, entity_data in [("Subject", subject_der), ("Issuer", issuer_der)]:
                for hash_name, hash_func in hash_functions.items():
                    key = hash_func(entity_data)
                    candidates.append((f"Cert_{entity_name}_{hash_name}", key))
            
            # Serial number
            try:
                serial_bytes = cert_obj.serial_number.to_bytes(16, 'big')[:16]
                candidates.append(("Cert_Serial", serial_bytes))
            except:
                pass
            
            # Public key
            try:
                pub_key_der = cert_obj.public_key().public_bytes(
                    encoding=serialization.Encoding.DER,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                )
                
                for hash_name, hash_func in hash_functions.items():
                    key = hash_func(pub_key_der)
                    candidates.append((f"Cert_PubKey_{hash_name}", key))
            except:
                pass
            
        except Exception as e:
            print(f"⚠️ X.509 parsing failed: {e}")
        
        # 3. Signature patterns
        signatures = self.extract_signature_patterns(cert_data)
        for i, sig in enumerate(signatures):
            candidates.append((f"Cert_Signature_{i}", sig))
        
        # 4. Static data combinations
        base_candidates = candidates[:15]  # First 15 base keys
        for name, base_key in base_candidates:
            # XOR with static IV
            xor_iv = bytes(a ^ b for a, b in zip(base_key, self.STATIC_IV))
            candidates.append((f"{name}_XOR_IV", xor_iv))
            
            # XOR with static data
            static_padded = (self.STATIC_DATA2 * 2)[:16]
            xor_static = bytes(a ^ b for a, b in zip(base_key, static_padded))
            candidates.append((f"{name}_XOR_Static", xor_static))
        
        # 5. PBKDF2 derived keys
        salt_sources = [
            b"NumberBox", b"android", b"hotcodes", b"encrypt",
            cert_data[:16], cert_data[-16:], self.STATIC_IV, self.STATIC_DATA2
        ]
        
        for salt in salt_sources:
            try:
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=16,
                    salt=salt,
                    iterations=1000,
                )
                derived_key = kdf.derive(cert_data[:32])
                candidates.append((f"PBKDF2_{salt.hex()[:8]}", derived_key))
            except:
                pass
        
        # 6. Certificate chunks with good entropy
        chunk_size = 16
        for i in range(0, min(len(cert_data), 512), 4):  # Check first 512 bytes
            if i + chunk_size <= len(cert_data):
                chunk = cert_data[i:i+chunk_size]
                if len(set(chunk)) >= 8:  # Good entropy
                    candidates.append((f"Cert_Chunk_{i:04x}", chunk))
        
        # 7. Hardware-specific patterns (Android specific)
        android_patterns = [
            b"AndroidDebugKey",
            b"Android",
            b"debug.keystore",
            b"androiddebugkey"
        ]
        
        for pattern in android_patterns:
            for hash_name, hash_func in hash_functions.items():
                combined = cert_data + pattern
                key = hash_func(combined)
                candidates.append((f"Android_{pattern.decode('ascii', errors='ignore')}_{hash_name}", key))
        
        print(f"📊 Generated {len(candidates)} key candidates")
        return candidates

    def extract_signature_patterns(self, cert_data):
        """Extract signature patterns from certificate"""
        patterns = []
        
        # RSA signature patterns
        for i in range(len(cert_data) - 16):
            if cert_data[i:i+2] == b'\x00\x01':
                sig_data = cert_data[i+2:i+18]
                if len(sig_data) == 16:
                    patterns.append(sig_data)
            
            # ASN.1 BIT STRING
            if cert_data[i] == 0x03:
                try:
                    length = cert_data[i+1]
                    if length < 0x80 and i+2+length <= len(cert_data):
                        sig_candidate = cert_data[i+2:i+2+min(16, length)]
                        if len(sig_candidate) == 16:
                            patterns.append(sig_candidate)
                except:
                    pass
        
        return patterns[:10]

    def comprehensive_attack(self):
        """Run comprehensive attack using all methods"""
        print("\n🚀 Starting comprehensive cryptanalysis...")
        
        if not self.certificate:
            print("❌ No certificate available")
            return False
        
        # Generate all key candidates
        key_candidates = self.generate_advanced_key_candidates()
        
        print(f"🔑 Testing {len(key_candidates)} key candidates...")
        
        partial_matches = []
        
        for i, (key_name, key) in enumerate(key_candidates):
            if i % 50 == 0:
                print(f"🔍 Progress: {i}/{len(key_candidates)} ({i/len(key_candidates)*100:.1f}%)")
            
            result = self.test_key_comprehensive(key, key_name)
            
            if isinstance(result, dict) and result.get('match'):
                print(f"\n🎉 SOLUTION FOUND!")
                self.working_solution = result
                return True
            elif isinstance(result, list) and result:
                partial_matches.extend(result)
        
        # Analyze partial matches
        if partial_matches:
            print(f"\n📊 Found {len(partial_matches)} partial matches:")
            
            # Sort by longest partial match
            partial_matches.sort(key=lambda x: x.get('partial_match', 0), reverse=True)
            
            for i, match in enumerate(partial_matches[:10]):
                print(f"  {i+1}. {match['key_name']} | {match['iv_method']} | {match['padding']} | Match: {match.get('partial_match', 0)} chars")
            
            # Try to improve best partial matches
            print(f"\n🔧 Analyzing best partial matches for patterns...")
            self.analyze_partial_matches(partial_matches[:5])
        
        print(f"\n❌ No complete solution found with current methods")
        return False

    def analyze_partial_matches(self, partial_matches):
        """Analyze partial matches to find patterns"""
        print(f"🔬 Analyzing {len(partial_matches)} partial matches...")
        
        for match in partial_matches:
            key_hex = match['key_hex']
            iv_method = match['iv_method']
            padding = match['padding']
            
            print(f"\n🧪 Analyzing: {match['key_name']}")
            print(f"   Key: {key_hex}")
            print(f"   Partial match: {match.get('partial_match', 0)} characters")
            
            # Try variations of the key
            base_key = bytes.fromhex(key_hex)
            
            key_variations = [
                ("Original", base_key),
                ("Reversed", base_key[::-1]),
                ("Rotated_Left", base_key[1:] + base_key[:1]),
                ("Rotated_Right", base_key[-1:] + base_key[:-1]),
                ("XOR_FF", bytes(b ^ 0xFF for b in base_key)),
                ("Incremented", bytes((b + 1) % 256 for b in base_key)),
                ("Decremented", bytes((b - 1) % 256 for b in base_key)),
            ]
            
            for var_name, var_key in key_variations:
                result = self.test_key_comprehensive(var_key, f"{match['key_name']}_{var_name}")
                if isinstance(result, dict) and result.get('match'):
                    print(f"🎉 VARIATION MATCH: {var_name}")
                    return True
        
        return False

    def manual_encrypt(self, plaintext, key_hex, iv_hex=None, padding="PKCS7"):
        """Manual encryption for testing custom keys"""
        try:
            key = bytes.fromhex(key_hex)
            iv = bytes.fromhex(iv_hex) if iv_hex else self.STATIC_IV
            
            plaintext_bytes = plaintext.encode('utf-8')
            
            if padding == "PKCS7":
                padded = pad(plaintext_bytes, 16)
            elif padding == "Zero":
                padded = plaintext_bytes + b'\x00' * (16 - len(plaintext_bytes) % 16)
            else:
                padded = plaintext_bytes
            
            cipher = AES.new(key, AES.MODE_CBC, iv)
            encrypted = cipher.encrypt(padded)
            result = base64.b64encode(encrypted).decode('ascii')
            
            print(f"🔧 Manual encryption:")
            print(f"   Plaintext: {plaintext}")
            print(f"   Key: {key_hex}")
            print(f"   IV: {iv_hex or self.STATIC_IV.hex()}")
            print(f"   Padding: {padding}")
            print(f"   Result: {result}")
            
            return result
            
        except Exception as e:
            print(f"❌ Manual encryption failed: {e}")
            return None

    def memory_keys_test(self, memory_keys):
        """Test keys extracted from Frida memory analysis"""
        print(f"🧠 Testing {len(memory_keys)} keys from memory analysis...")
        
        for i, key_hex in enumerate(memory_keys):
            try:
                if len(key_hex) == 32:  # 16 bytes = 32 hex chars
                    key = bytes.fromhex(key_hex)
                    result = self.test_key_comprehensive(key, f"Memory_Key_{i}")
                    
                    if isinstance(result, dict) and result.get('match'):
                        print(f"🎉 MEMORY KEY MATCH!")
                        return True
                        
            except Exception as e:
                continue
        
        return False

def main():
    print("🔥 Advanced NumberBox Cryptanalysis Tool")
    print("=" * 50)
    
    # Find APK file
    apk_files = [f for f in os.listdir('.') if f.endswith('.apk')]
    
    if not apk_files:
        print("❌ No APK file found")
        return
    
    apk_path = apk_files[0]
    print(f"📱 Using APK: {apk_path}")
    
    crypto = AdvancedNumberBoxCrypto(apk_path)
    
    # Run comprehensive attack
    success = crypto.comprehensive_attack()
    
    if success:
        print(f"\n🎉 SUCCESS! Algorithm cracked!")
        if hasattr(crypto, 'working_solution'):
            sol = crypto.working_solution
            print(f"📋 Working solution:")
            print(f"   Key: {sol['key_hex']}")
            print(f"   IV Method: {sol['iv_method']}")
            print(f"   Padding: {sol['padding']}")
    else:
        print(f"\n🤔 Solution not found with current methods")
        print(f"💡 Next steps:")
        print(f"   1. Run enhanced Frida script to capture memory keys")
        print(f"   2. Analyze PlusAES library implementation details")
        print(f"   3. Check for hardware-specific key derivation")
        
        # Test manual key if provided
        print(f"\n🔧 Manual testing available:")
        print(f"   crypto.manual_encrypt('plaintext', 'key_hex', 'iv_hex')")

if __name__ == "__main__":
    main()