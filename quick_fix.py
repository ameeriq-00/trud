"""
إصلاح سريع لمشكلة العلاقات في قاعدة البيانات
قم بتشغيل هذا الملف لحل المشكلة
"""
import os
import sqlite3

def fix_database_relations():
    """إصلاح العلاقات في قاعدة البيانات"""
    
    print("🔧 بدء إصلاح قاعدة البيانات...")
    
    # حذف قاعدة البيانات الحالية إذا كانت موجودة
    db_path = "data/database.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        print("🗑️ تم حذف قاعدة البيانات القديمة")
    
    # إعادة إنشاء قاعدة البيانات
    try:
        from app.core.database import init_db
        init_db()
        print("✅ تم إنشاء قاعدة البيانات الجديدة بنجاح")
        
        # إنشاء حساب تجريبي
        create_test_account()
        
    except Exception as e:
        print(f"❌ خطأ في إنشاء قاعدة البيانات: {str(e)}")


def create_test_account():
    """إنشاء حساب تجريبي"""
    try:
        from app.core.database import SessionLocal
        from app.models.account import Account
        
        db = SessionLocal()
        
        # التحقق من وجود حساب تجريبي
        existing_account = db.query(Account).filter(Account.name == "test_account").first()
        
        if not existing_account:
            test_account = Account(
                name="test_account",
                token="eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6IjA5MDIxNjVkMDAxM2JiZGFlMThlNzQ1ZDRiNWY3OGMwNTk1OWJjODYzNjQxZWMxMGJjYzI1MmFjOWUxN2RjZmVjN2UwN2ZhMDVlOTc4YjhiIn0.eyJhdWQiOiIxIiwianRpIjoiMDkwMjE2NWQwMDEzYmJkYWUxOGU3NDVkNGI1Zjc4YzA1OTU5YmM4NjM2NDFlYzEwYmNjMjUyYWM5ZTE3ZGNmZWM3ZTA3ZmEwNWU5NzhiOGIiLCJpYXQiOjE3NTQ5NTc2MjEsIm5iZiI6MTc1NDk1NzYyMSwiZXhwIjoxNzg2NDkzNjIxLCJzdWIiOiIyNTkxNTAwIiwic2NvcGVzIjpbXX0.dhpLYUFCAbCk87KmI0HR-qi5NdJw80fmWlJYBkLjv8pqWau7ldWdxdNx6_wurgP-porQXAMsdRrKq_r07KRRkCdI0TSvPiT7oZbr4_ONpBjo1yjWaatrY5VGZscq1h-bN3xd-BfM0KbLsBYiiv_6nz76wUZhcWWqTL_I6H8kXqwm8wS2kD-CiY2X0KeG7Qm1_roSnUWO1X2fP3_VM5GvnL3AYVHr-vZdNn1D2YQRhnuBrgc3LXFrlONiiuf_X1gDXIykejhdU43A9NBBNCvjANm5-jMtKFCctrwohnT2s5BgcdCtQ3clr0fV_eRNtSkWDbHfkwHtXchCEC6rhnxsnwQAa5967BwG2rQoUgA8abWvH3gLh6guEg2AbmmFVKboXnCsZKF0ksHGuYTOEHKLzSFAbXsXR9QKTVOw3Vr1IIllJcTuLFH7hq-ASgpQlb75evmUiAJ78PHEEt6V-UDfn6GMV9hNEj4oFl1R2fTX5vaC7aur28q9Mj3XIX_SH-SB1FulwEYLUf5K0xPXtpaQXnOCfciHe1VWp7FPZBa6aWVW-g3fAiczYS0OH5xJgcNz3z0QM8RM4ixZH4xY-Io3Scby8tTM7d6u-EBYUM2NpiRaBrhK2TtFsmHszsGArcMoIQjzJHrvhiUVlnt7BkZblFchMT0AMhxLkiR8Rlu-06A",
                device_id="e89fdbf136ae2460",
                player_id="df33b4ce-9b1e-49ed-8ce0-44f1dbc89988",
                country="IQ",
                locale="ar",
                is_active=True
            )
            
            db.add(test_account)
            db.commit()
            print("✅ تم إنشاء حساب تجريبي")
        
        db.close()
        
    except Exception as e:
        print(f"❌ خطأ في إنشاء الحساب التجريبي: {str(e)}")


if __name__ == "__main__":
    fix_database_relations()
    print("🎉 تم الانتهاء من الإصلاح!")
    print("يمكنك الآن تشغيل python run.py مرة أخرى")