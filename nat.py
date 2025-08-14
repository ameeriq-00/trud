#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Native Library Analysis Tool - تحليل libnative-lib.so لاستخراج المفاتيح
"""

import os
import re
import binascii
import struct
from pathlib import Path

def analyze_native_library(lib_path):
    """تحليل المكتبة المحلية الشامل"""
    print(f"🔍 Analyzing: {lib_path}")
    
    if not os.path.exists(lib_path):
        print(f"❌ File not found: {lib_path}")
        return []
    
    with open(lib_path, 'rb') as f:
        data = f.read()
    
    print(f"📊 File size: {len(data)} bytes")
    
    keys_found = []
    
    # 1. البحث عن AES S-Box patterns
    keys_found.extend(find_aes_sbox_keys(data))
    
    # 2. البحث عن hex patterns
    keys_found.extend(find_hex_patterns(data))
    
    # 3. البحث عن hardcoded arrays
    keys_found.extend(find_hardcoded_arrays(data))
    
    # 4. البحث عن strings
    keys_found.extend(find_key_strings(data))
    
    # 5. البحث عن PlusAES patterns
    keys_found.extend(find_plusaes_patterns(data))
    
    return keys_found

def find_aes_sbox_keys(data):
    """البحث عن مفاتيح بالقرب من AES S-Box"""
    print("🔍 Searching near AES S-Box...")
    
    # AES S-Box signature
    sbox_pattern = bytes([
        0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5,
        0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76
    ])
    
    keys = []
    sbox_pos = data.find(sbox_pattern)
    
    if sbox_pos != -1:
        print(f"✅ Found AES S-Box at offset: 0x{sbox_pos:x}")
        
        # البحث في المنطقة المحيطة
        search_start = max(0, sbox_pos - 1024)
        search_end = min(len(data), sbox_pos + 1024)
        
        for offset in range(search_start, search_end - 16, 4):
            key_candidate = data[offset:offset+16]
            if is_potential_key(key_candidate):
                hex_key = key_candidate.hex()
                keys.append({
                    'key': hex_key,
                    'source': f'near_sbox_0x{offset:x}',
                    'confidence': 'high'
                })
                print(f"🗝️ Key near S-Box: {hex_key}")
    
    return keys

def find_hex_patterns(data):
    """البحث عن hex patterns"""
    print("🔍 Searching for hex patterns...")
    
    keys = []
    
    # البحث عن 32-char hex strings
    hex_pattern = rb'[0-9A-Fa-f]{32}'
    matches = re.finditer(hex_pattern, data)
    
    for match in matches:
        try:
            hex_str = match.group().decode('ascii')
            if len(hex_str) == 32:  # 16 bytes = 32 hex chars
                keys.append({
                    'key': hex_str.lower(),
                    'source': f'hex_string_0x{match.start():x}',
                    'confidence': 'medium'
                })
                print(f"🗝️ Hex pattern: {hex_str.lower()}")
        except:
            pass
    
    return keys

def find_hardcoded_arrays(data):
    """البحث عن hardcoded arrays"""
    print("🔍 Searching for hardcoded arrays...")
    
    keys = []
    
    # البحث عن patterns مثل: {0x12, 0x34, 0x56, ...}
    for i in range(0, len(data) - 16, 4):
        key_candidate = data[i:i+16]
        
        if is_potential_key(key_candidate):
            # فحص إذا كانت محاطة بـ null bytes (تدل على array)
            before = data[max(0, i-4):i] if i >= 4 else b''
            after = data[i+16:i+20] if i+20 < len(data) else b''
            
            if (b'\x00' in before or b'\x00' in after):
                hex_key = key_candidate.hex()
                keys.append({
                    'key': hex_key,
                    'source': f'hardcoded_array_0x{i:x}',
                    'confidence': 'high'
                })
                print(f"🗝️ Hardcoded array: {hex_key}")
    
    return keys

def find_key_strings(data):
    """البحث عن key strings"""
    print("🔍 Searching for key strings...")
    
    keys = []
    
    # البحث عن strings قابلة للقراءة
    string_pattern = rb'[\x20-\x7E]{16,64}'
    matches = re.finditer(string_pattern, data)
    
    for match in matches:
        try:
            string = match.group().decode('ascii')
            
            # فحص keywords
            key_indicators = ['key', 'secret', 'pass', 'aes', 'encrypt', 
                             'numberbox', 'hotcodes', 'android', 'samsung']
            
            if any(indicator in string.lower() for indicator in key_indicators):
                if len(string) >= 16:
                    # استخدام أول 16 character كمفتاح
                    key_bytes = string[:16].encode('ascii')
                    hex_key = key_bytes.hex()
                    
                    keys.append({
                        'key': hex_key,
                        'source': f'key_string_0x{match.start():x}',
                        'confidence': 'medium',
                        'original': string
                    })
                    print(f"🗝️ Key string: {hex_key} ('{string}')")
        except:
            pass
    
    return keys

def find_plusaes_patterns(data):
    """البحث عن PlusAES specific patterns"""
    print("🔍 Searching for PlusAES patterns...")
    
    keys = []
    
    # PlusAES function signatures
    plusaes_patterns = [
        b'PlusAES',
        b'aes_encrypt',
        b'aes_decrypt',
        b'aes_key_expand',
        b'rijndael'
    ]
    
    for pattern in plusaes_patterns:
        pos = data.find(pattern)
        if pos != -1:
            print(f"✅ Found PlusAES pattern '{pattern.decode()}' at 0x{pos:x}")
            
            # البحث في المنطقة المحيطة
            search_start = max(0, pos - 512)
            search_end = min(len(data), pos + 512)
            
            for offset in range(search_start, search_end - 16, 4):
                key_candidate = data[offset:offset+16]
                if is_potential_key(key_candidate):
                    hex_key = key_candidate.hex()
                    keys.append({
                        'key': hex_key,
                        'source': f'plusaes_0x{offset:x}',
                        'confidence': 'high'
                    })
                    print(f"🗝️ PlusAES key: {hex_key}")
    
    return keys

def is_potential_key(data):
    """فحص إذا كانت البيانات تبدو مثل مفتاح AES"""
    if len(data) != 16:
        return False
    
    # يجب أن تحتوي على تنوع جيد
    unique_bytes = len(set(data))
    if unique_bytes < 8:
        return False
    
    # لا يجب أن تكون كلها null أو 0xFF
    if data == b'\x00' * 16 or data == b'\xFF' * 16:
        return False
    
    # فحص entropy بسيط
    zero_count = data.count(0)
    if zero_count > 12:  # أكثر من 75% أصفار
        return False
    
    return True

def extract_keys_with_ghidra_format(lib_path):
    """استخراج مفاتيح بتنسيق Ghidra-friendly"""
    print("\n🔧 Ghidra Analysis Guide:")
    print("1. Open libnative-lib.so in Ghidra")
    print("2. Search for:")
    print("   - Function: Java_com_hotcodes_numberbox_features_cryption_Encrypt_encrypt")
    print("   - Strings: 'aes', 'encrypt', 'key'")
    print("   - Data: AES S-Box (63 7c 77 7b f2 6b 6f c5)")
    print("3. Look for:")
    print("   - 16-byte arrays near encryption functions")
    print("   - XOR operations with constants")
    print("   - Memory allocations of 16 bytes")

def main():
    """الدالة الرئيسية"""
    print("🔥 Native Library Analysis Tool")
    print("=" * 50)
    
    # مسارات محتملة للمكتبة
    lib_paths = [
        "libnative-lib.so",
        "lib/arm64-v8a/libnative-lib.so",
        "lib/armeabi-v7a/libnative-lib.so",
        "native-lib.so"
    ]
    
    lib_found = None
    for path in lib_paths:
        if os.path.exists(path):
            lib_found = path
            break
    
    if not lib_found:
        print("❌ libnative-lib.so not found!")
        print("💡 Download it from the APK:")
        print("1. Extract NumberBox APK")
        print("2. Navigate to lib/arm64-v8a/ or lib/armeabi-v7a/")
        print("3. Copy libnative-lib.so to current directory")
        extract_keys_with_ghidra_format("")
        return
    
    # تحليل المكتبة
    all_keys = analyze_native_library(lib_found)
    
    if all_keys:
        print(f"\n🎉 Found {len(all_keys)} potential keys!")
        print("\n📋 [NATIVE KEYS SUMMARY]")
        
        for i, key_info in enumerate(all_keys):
            confidence = key_info.get('confidence', 'unknown')
            source = key_info.get('source', 'unknown')
            key = key_info['key']
            
            print(f"{i+1}. {source} ({confidence}): {key}")
            
            if 'original' in key_info:
                print(f"   Original: '{key_info['original']}'")
        
        # كتابة المفاتيح لملف للاختبار
        with open('native_keys.txt', 'w') as f:
            for key_info in all_keys:
                f.write(f"{key_info['key']}\n")
        
        print(f"\n💾 Keys saved to 'native_keys.txt'")
        print("💡 Add these keys to your Python decryptor!")
        
    else:
        print("\n❌ No keys found in native library")
        print("\n💡 Try:")
        print("1. Use the memory dump Frida script")
        print("2. Analyze with Ghidra manually")
        print("3. Hook AES functions directly")
    
    extract_keys_with_ghidra_format(lib_found)

if __name__ == "__main__":
    main()