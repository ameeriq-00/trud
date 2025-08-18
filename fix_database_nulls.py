"""
إصلاح قيم NULL في قاعدة البيانات
"""
import sqlite3
import os
from datetime import datetime

def fix_database_nulls():
    """إصلاح قيم NULL في قاعدة البيانات"""
    
    db_path = "data/database.db"
    
    if not os.path.exists(db_path):
        print("❌ قاعدة البيانات غير موجودة")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔧 إصلاح قيم NULL في جدول api_keys...")
        
        # تحديث القيم الفارغة
        cursor.execute("""
            UPDATE api_keys 
            SET usage_count = 0 
            WHERE usage_count IS NULL
        """)
        
        affected_rows = cursor.rowcount
        print(f"✅ تم تحديث {affected_rows} سجل")
        
        # التأكد من وجود مفتاح للاختبار
        cursor.execute("SELECT COUNT(*) FROM api_keys WHERE is_active = 1")
        active_keys = cursor.fetchone()[0]
        
        if active_keys == 0:
            print("🔑 إضافة مفتاح اختبار...")
            api_key = "hc_test_development_key_12345"
            current_time = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO api_keys (name, key, description, is_active, usage_count, created_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                "development_key",
                api_key, 
                "مفتاح التطوير",
                1,  # True
                0,  # usage_count
                "admin",
                current_time
            ))
            
            print(f"✅ تم إضافة مفتاح: {api_key}")
        
        # عرض المفاتيح الموجودة
        cursor.execute("SELECT id, name, key, is_active, usage_count FROM api_keys")
        keys = cursor.fetchall()
        
        print(f"\n📋 المفاتيح الموجودة ({len(keys)}):")
        for key in keys:
            key_display = key[2][:20] + "..." if len(key[2]) > 20 else key[2]
            print(f"   ID: {key[0]}, Name: {key[1]}, Key: {key_display}, Active: {key[3]}, Usage: {key[4]}")
        
        conn.commit()
        conn.close()
        
        print("✅ تم إصلاح قاعدة البيانات بنجاح!")
        
    except Exception as e:
        print(f"❌ خطأ: {str(e)}")

if __name__ == "__main__":
    fix_database_nulls()