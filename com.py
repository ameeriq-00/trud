#!/usr/bin/env python3
"""
🔥 Complete NumberBox Solution - Final Comprehensive Tool
Combines all analysis methods for complete reverse engineering
"""

import re
import base64
import hashlib
import zipfile
import os
import struct
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from cryptography import x509

class CompleteNumberBoxSolution:
    def __init__(self, apk_path=None):
        # Known constants
        self.STATIC_IV = bytes.fromhex("0F0E0D0C0B0A09080706050403020100")
        self.STATIC_DATA2 = bytes.fromhex("10000000100000001000000010")
        
        # Test cases
        self.TEST_CASES = [
            ("+964", "zn92OT0dWHbvH2UTB01naJHL6aqsusUleB"),
            ("7809394930", "7K1MaGp9+EXKitK2U/8n4DDjbe/96r0aSK")
        ]
        
        # Data storage
        self.found_keys = set()
        self.memory_patterns = []
        self.certificate = None
        self.working_solution = None
        
        # Load certificate if APK provided
        if apk_path and os.path.exists(apk_path):
            self.certificate = self.extract_certificate(apk_path)
        
        print(f"🔒 Static IV: {self.STATIC_IV.hex()}")
        print(f"🔒 Static Data: {self.STATIC_DATA2.hex()}")
    
    def extract_certificate(self, apk_path):
        """Extract certificate from APK"""
        try:
            with zipfile.ZipFile(apk_path, 'r') as apk:
                cert_files = [f for f in apk.namelist() 
                             if 'META-INF' in f and f.endswith('.RSA')]
                
                if cert_files:
                    cert_data = apk.read(cert_files[0])
                    print(f"✅ Certificate extracted: {len(cert_data)} bytes")
                    return cert_data
                else:
                    print("❌ No certificate found")
                    return None
        except Exception as e:
            print(f"❌ Certificate extraction error: {e}")
            return None
    
    def parse_frida_output(self, frida_log_file):
        """Parse Frida output from file or string"""
        
        print("🔍 Parsing Frida output...")
        
        if os.path.exists(frida_log_file):
            with open(frida_log_file, 'r') as f:
                frida_log = f.read()
        else:
            frida_log = frida_log_file  # Assume it's the log content itself
        
        # Extract potential keys
        key_patterns = [
            r'🗝️.*?([a-fA-F0-9]{32})',
            r'Key.*?([a-fA-F0-9]{32})',
            r'arg\d+.*?([a-fA-F0-9]{32})',
            r'Data.*?([a-fA-F0-9]{32,})',
        ]
        
        for pattern in key_patterns:
            matches = re.findall(pattern, frida_log, re.IGNORECASE)
            for match in matches:
                if len(match) >= 32:
                    # Extract 16-byte chunks
                    for i in range(0, len(match) - 31, 32):
                        chunk = match[i:i+32]
                        if len(chunk) == 32:
                            self.found_keys.add(chunk.upper())
        
        # Extract memory patterns
        memory_pattern = r'Data at 0x([a-fA-F0-9]+): ([a-fA-F0-9]+)'
        memory_matches = re.findall(memory_pattern, frida_log)
        
        for address, data in memory_matches:
            self.memory_patterns.append({
                'address': address,
                'data': data.upper()
            })
        
        print(f"📊 Extracted {len(self.found_keys)} potential keys")
        print(f"📊 Extracted {len(self.memory_patterns)} memory patterns")
        
        return len(self.found_keys) > 0
    
    def generate_certificate_keys(self):
        """Generate keys from certificate analysis"""
        
        if not self.certificate:
            return []
        
        cert_keys = []
        cert_data = self.certificate
        
        # Hash-based keys
        hash_functions = {
            'MD5': lambda data: hashlib.md5(data).digest()[:16],
            'SHA1': lambda data: hashlib.sha1(data).digest()[:16],
            'SHA256': lambda data: hashlib.sha256(data).digest()[:16],
        }
        
        for name, hash_func in hash_functions.items():
            key = hash_func(cert_data)
            cert_keys.append(key.hex().upper())
        
        # Certificate structure analysis
        try:
            cert_obj = x509.load_der_x509_certificate(cert_data)
            
            # Subject hash
            subject_der = cert_obj.subject.public_bytes()
            for name, hash_func in hash_functions.items():
                key = hash_func(subject_der)
                cert_keys.append(key.hex().upper())
            
            # Serial number
            try:
                serial_bytes = cert_obj.serial_number.to_bytes(16, 'big')[:16]
                cert_keys.append(serial_bytes.hex().upper())
            except:
                pass
                
        except:
            pass
        
        # Certificate chunks
        for i in range(0, min(len(cert_data), 256), 16):
            if i + 16 <= len(cert_data):
                chunk = cert_data[i:i+16]
                cert_keys.append(chunk.hex().upper())
        
        print(f"🔑 Generated {len(cert_keys)} certificate-based keys")
        return cert_keys
    
    def test_all_keys(self):
        """Test all collected keys comprehensively"""
        
        print("🧪 Testing all collected keys...")
        
        # Combine all key sources
        all_keys = set(self.found_keys)
        
        # Add certificate keys
        cert_keys = self.generate_certificate_keys()
        all_keys.update(cert_keys)
        
        # Add memory pattern keys
        for pattern in self.memory_patterns:
            data = pattern['data']
            for i in range(0, len(data) - 31, 2):
                chunk = data[i:i+32]
                if len(chunk) == 32:
                    all_keys.add(chunk)
        
        print(f"🔍 Testing {len(all_keys)} unique keys...")
        
        # Test configurations
        iv_configs = [
            ("Static_IV", self.STATIC_IV),
            ("Zero_IV", b'\x00' * 16),
            ("Key_as_IV", None),  # Will be set to key
        ]
        
        tested = 0
        for key_hex in all_keys:
            tested += 1
            if tested % 50 == 0:
                print(f"   Progress: {tested}/{len(all_keys)} ({tested/len(all_keys)*100:.1f}%)")
            
            try:
                key = bytes.fromhex(key_hex)
                if len(key) != 16:
                    continue
                
                for iv_name, iv in iv_configs:
                    current_iv = key if iv is None else iv
                    
                    for plaintext, expected in self.TEST_CASES:
                        try:
                            plaintext_bytes = plaintext.encode('utf-8')
                            padded = pad(plaintext_bytes, 16)
                            
                            cipher = AES.new(key, AES.MODE_CBC, current_iv)
                            encrypted = cipher.encrypt(padded)
                            result = base64.b64encode(encrypted).decode('ascii')
                            
                            if result == expected:
                                print(f"\n🎉 PERFECT MATCH FOUND!")
                                print(f"   Key: {key_hex}")
                                print(f"   IV: {iv_name} ({current_iv.hex()})")
                                print(f"   Test: {plaintext} -> {result}")
                                
                                self.working_solution = {
                                    'key_hex': key_hex,
                                    'key_bytes': key,
                                    'iv_method': iv_name,
                                    'iv_hex': current_iv.hex(),
                                    'iv_bytes': current_iv
                                }
                                
                                return True
                            
                            # Check for partial matches
                            match_len = 0
                            for i in range(min(len(result), len(expected))):
                                if result[i] == expected[i]:
                                    match_len += 1
                                else:
                                    break
                            
                            if match_len >= 15:  # Significant partial match
                                print(f"⚡ Strong partial match: {key_hex[:16]}... | {iv_name} | {match_len} chars")
                        
                        except Exception:
                            continue
            
            except Exception:
                continue
        
        return False
    
    def encrypt_with_solution(self, plaintext):
        """Encrypt using found solution"""
        
        if not self.working_solution:
            print("❌ No working solution found")
            return None
        
        try:
            key = self.working_solution['key_bytes']
            iv = self.working_solution['iv_bytes']
            
            plaintext_bytes = plaintext.encode('utf-8')
            padded = pad(plaintext_bytes, 16)
            
            cipher = AES.new(key, AES.MODE_CBC, iv)
            encrypted = cipher.encrypt(padded)
            result = base64.b64encode(encrypted).decode('ascii')
            
            print(f"🔐 Encrypted '{plaintext}' -> '{result}'")
            return result
            
        except Exception as e:
            print(f"❌ Encryption failed: {e}")
            return None
    
    def create_api_function(self):
        """Create reusable API function"""
        
        if not self.working_solution:
            print("❌ No solution available for API creation")
            return None
        
        key_hex = self.working_solution['key_hex']
        iv_hex = self.working_solution['iv_hex']
        
        api_code = f'''
def numberbox_encrypt(phone_number):
    """
    NumberBox phone number encryption function
    
    Args:
        phone_number (str): Phone number to encrypt (e.g., "+964" or "7809394930")
    
    Returns:
        str: Base64 encoded encrypted phone number
    """
    import base64
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad
    
    # Extracted encryption parameters
    KEY = bytes.fromhex('{key_hex}')
    IV = bytes.fromhex('{iv_hex}')
    
    try:
        # Convert to bytes and pad
        plaintext_bytes = phone_number.encode('utf-8')
        padded = pad(plaintext_bytes, 16)
        
        # Encrypt using AES-CBC
        cipher = AES.new(KEY, AES.MODE_CBC, IV)
        encrypted = cipher.encrypt(padded)
        
        # Return base64 encoded result
        return base64.b64encode(encrypted).decode('ascii')
        
    except Exception as e:
        raise Exception(f"Encryption failed: {{e}}")

# Test the function
if __name__ == "__main__":
    # Test cases
    test_cases = [
        ("+964", "zn92OT0dWHbvH2UTB01naJHL6aqsusUleB"),
        ("7809394930", "7K1MaGp9+EXKitK2U/8n4DDjbe/96r0aSK")
    ]
    
    print("🧪 Testing API function:")
    for plaintext, expected in test_cases:
        result = numberbox_encrypt(plaintext)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"   {{plaintext}} -> {{result}} {{status}}")
'''
        
        return api_code
    
    def save_solution(self, filename="numberbox_solution.py"):
        """Save the working solution to a file"""
        
        if not self.working_solution:
            print("❌ No solution to save")
            return False
        
        try:
            api_code = self.create_api_function()
            
            with open(filename, 'w') as f:
                f.write(api_code)
            
            print(f"💾 Solution saved to {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to save solution: {e}")
            return False
    
    def run_complete_analysis(self, frida_log=None):
        """Run complete analysis pipeline"""
        
        print("\n🚀 Starting complete NumberBox analysis...")
        print("=" * 60)
        
        # Step 1: Parse Frida output if provided
        if frida_log:
            print("\n📋 Step 1: Parsing Frida output")
            self.parse_frida_output(frida_log)
        else:
            print("\n⚠️ No Frida output provided, using certificate analysis only")
        
        # Step 2: Test all keys
        print("\n🧪 Step 2: Testing all collected keys")
        success = self.test_all_keys()
        
        if success:
            print(f"\n🎉 SUCCESS! NumberBox encryption cracked!")
            print(f"📋 Solution details:")
            sol = self.working_solution
            print(f"   Key: {sol['key_hex']}")
            print(f"   IV Method: {sol['iv_method']}")
            print(f"   IV: {sol['iv_hex']}")
            
            # Step 3: Create API function
            print(f"\n📦 Step 3: Creating reusable API")
            api_code = self.create_api_function()
            
            # Step 4: Save solution
            print(f"\n💾 Step 4: Saving solution")
            self.save_solution()
            
            # Step 5: Test with custom input
            print(f"\n🧪 Step 5: Testing with custom inputs")
            test_numbers = ["+9647801234567", "7801234567", "+1234567890"]
            
            for number in test_numbers:
                encrypted = self.encrypt_with_solution(number)
                if encrypted:
                    print(f"   {number} -> {encrypted}")
            
            return True
        
        else:
            print(f"\n❌ Solution not found")
            print(f"💡 Troubleshooting suggestions:")
            print(f"   1. Ensure Frida captured the actual encryption calls")
            print(f"   2. Try running the enhanced Frida script during encryption")
            print(f"   3. Check if the app uses additional obfuscation")
            print(f"   4. Verify the test cases are still valid")
            
            return False

def main():
    print("🔥 Complete NumberBox Reverse Engineering Solution")
    print("=" * 60)
    
    # Check for APK file
    apk_files = [f for f in os.listdir('.') if f.endswith('.apk')]
    apk_path = apk_files[0] if apk_files else None
    
    if apk_path:
        print(f"📱 Found APK: {apk_path}")
    else:
        print("⚠️ No APK file found, certificate analysis will be skipped")
    
    # Initialize solution
    solution = CompleteNumberBoxSolution(apk_path)
    
    # Check for Frida log file
    frida_logs = [f for f in os.listdir('.') if 'frida' in f.lower() and f.endswith('.log')]
    frida_log = frida_logs[0] if frida_logs else None
    
    if frida_log:
        print(f"📋 Found Frida log: {frida_log}")
    else:
        print("⚠️ No Frida log found, place your frida output in a .log file")
    
    # Run complete analysis
    success = solution.run_complete_analysis(frida_log)
    
    if success:
        print(f"\n🎊 Analysis completed successfully!")
        print(f"📂 Check 'numberbox_solution.py' for the working API function")
    else:
        print(f"\n🔧 Manual testing available:")
        print(f"   solution.encrypt_with_solution('your_number')")
        print(f"   solution.test_all_keys()")
    
    return solution

if __name__ == "__main__":
    solution = main()