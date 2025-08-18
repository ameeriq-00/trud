"""
إصلاح بسيط لإضافة API Key مباشرة في قاعدة البيانات
"""
import sqlite3
import os
from datetime import datetime

def add_api_key_directly():
    """إضافة API Key مباشرة في قاعدة البيانات"""
    
    db_path = "data/database.db"
    
    if not os.path.exists(db_path):
        print("❌ قاعدة البيانات غير موجودة")
        return
    
    try:
        # الاتصال بقاعدة البيانات
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # حذف المفاتيح القديمة
        cursor.execute("DELETE FROM api_keys")
        
        # إضافة مفتاح جديد
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
        
        conn.commit()
        conn.close()
        
        print("✅ تم إضافة API Key بنجاح!")
        print(f"🔑 API Key: {api_key}")
        print("\n📋 الآن يمكنك اختبار API:")
        print(f"   Header: Authorization: Bearer {api_key}")
        
        return api_key
        
    except Exception as e:
        print(f"❌ خطأ: {str(e)}")
        return None

if __name__ == "__main__":
    add_api_key_directly()