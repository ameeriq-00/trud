"""
فحص API Keys الموجودة في قاعدة البيانات
"""
import sqlite3
import os

def check_existing_api_keys():
    """فحص المفاتيح الموجودة"""
    
    db_path = "data/database.db"
    
    if not os.path.exists(db_path):
        print("❌ قاعدة البيانات غير موجودة")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # فحص بنية الجدول
        cursor.execute("PRAGMA table_info(api_keys)")
        columns = cursor.fetchall()
        print("📋 أعمدة جدول api_keys:")
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")
        
        # فحص المفاتيح الموجودة
        cursor.execute("SELECT * FROM api_keys")
        keys = cursor.fetchall()
        
        print(f"\n🔑 عدد المفاتيح الموجودة: {len(keys)}")
        
        if keys:
            print("📜 المفاتيح الموجودة:")
            for key in keys:
                print(f"   ID: {key[0]}, Name: {key[1]}, Key: {key[2][:20]}..., Active: {key[4]}")
        else:
            print("⚠️ لا توجد مفاتيح في قاعدة البيانات")
            
            # إضافة مفتاح جديد
            print("🔧 إضافة مفتاح جديد...")
            add_test_key(cursor)
            conn.commit()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ خطأ: {str(e)}")

def add_test_key(cursor):
    """إضافة مفتاح اختبار"""
    from datetime import datetime
    
    api_key = "hc_test_development_key_12345"
    current_time = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO api_keys (name, key, description, is_active, created_by, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        "development_key",
        api_key, 
        "مفتاح التطوير",
        1,  # True
        "admin",
        current_time
    ))
    
    print(f"✅ تم إضافة مفتاح: {api_key}")

if __name__ == "__main__":
    check_existing_api_keys()