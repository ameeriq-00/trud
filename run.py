#!/usr/bin/env python3
"""
TRUD - HelloCallers Proxy
ملف تشغيل التطبيق الرئيسي
"""

import os
import sys
import uvicorn
import argparse
from pathlib import Path

# إضافة مجلد التطبيق لمسار Python
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from app.main import app


def setup_logging():
    """إعداد نظام التسجيل"""
    import logging
    
    # إنشاء مجلد اللوغات إذا لم يكن موجوداً
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # إعداد التسجيل
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(settings.LOG_FILE, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    # تقليل مستوى تسجيل مكتبات معينة
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    if not settings.DEBUG:
        logging.getLogger("uvicorn").setLevel(logging.WARNING)


def check_dependencies():
    """فحص التبعيات المطلوبة"""
    required_packages = [
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("sqlalchemy", "sqlalchemy"),
        ("pydantic", "pydantic"),
        ("httpx", "httpx"),
        ("jinja2", "jinja2"),
        ("python-multipart", "multipart"),
        ("passlib", "passlib"),
        ("python-jose", "jose"),
        ("cryptography", "cryptography"),
        ("phonenumbers", "phonenumbers"),
        ("pydantic-settings", "pydantic_settings")
    ]
    
    missing_packages = []
    
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        print("❌ المكتبات التالية مفقودة:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nلتثبيت المكتبات المفقودة:")
        print(f"pip install {' '.join(missing_packages)}")
        sys.exit(1)


def create_directories():
    """إنشاء المجلدات المطلوبة"""
    directories = [
        "data",
        "logs", 
        "static/css",
        "static/js",
        "static/images",
        "templates",
        "backups"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ تم إنشاء المجلد: {directory}")


def print_banner():
    """طباعة معلومات التطبيق"""
    banner = f"""
╔══════════════════════════════════════════════════════════════╗
║                    TRUD - HelloCallers Proxy                ║
║                        الإصدار {settings.VERSION}                         ║
╠══════════════════════════════════════════════════════════════╣
║  نظام بروكسي متقدم لـ HelloCallers API                      ║
║  مع إمكانيات البحث المجمع والإدارة الذكية                   ║
╚══════════════════════════════════════════════════════════════╝

🔧 الإعدادات:
   • الخادم: {settings.HOST}:{settings.PORT}
   • قاعدة البيانات: {settings.DATABASE_URL}
   • وضع التطوير: {'مُفعل' if settings.DEBUG else 'مُعطل'}
   • مستوى التسجيل: {settings.LOG_LEVEL}

🌐 الواجهات:
   • لوحة التحكم: http://{settings.HOST}:{settings.PORT}/
   • واجهة API: http://{settings.HOST}:{settings.PORT}/api/docs
   • مراقبة الصحة: http://{settings.HOST}:{settings.PORT}/health

🔑 معلومات تسجيل الدخول الافتراضية:
   • اسم المستخدم: {settings.ADMIN_USERNAME}
   • كلمة المرور: {settings.ADMIN_PASSWORD}

{'⚠️  تحذير: يرجى تغيير كلمة المرور الافتراضية في الإنتاج!' if settings.ADMIN_PASSWORD == 'admin123' else ''}
"""
    print(banner)


def check_port_availability(port: int) -> bool:
    """فحص إتاحة المنفذ"""
    import socket
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('', port))
            return True
        except OSError:
            return False


def main():
    """الدالة الرئيسية"""
    parser = argparse.ArgumentParser(description="TRUD - HelloCallers Proxy Server")
    parser.add_argument("--host", default=settings.HOST, help="عنوان IP للخادم")
    parser.add_argument("--port", type=int, default=settings.PORT, help="منفذ الخادم")
    parser.add_argument("--reload", action="store_true", help="تفعيل إعادة التحميل التلقائي")
    parser.add_argument("--workers", type=int, default=1, help="عدد العمليات")
    parser.add_argument("--log-level", default=settings.LOG_LEVEL.lower(), 
                       choices=["critical", "error", "warning", "info", "debug"],
                       help="مستوى التسجيل")
    parser.add_argument("--ssl-keyfile", help="ملف المفتاح الخاص SSL")
    parser.add_argument("--ssl-certfile", help="ملف شهادة SSL")
    parser.add_argument("--check", action="store_true", help="فحص النظام فقط")
    parser.add_argument("--init-db", action="store_true", help="تهيئة قاعدة البيانات فقط")
    
    args = parser.parse_args()
    
    try:
        # فحص التبعيات
        print("🔍 فحص التبعيات...")
        check_dependencies()
        print("✅ جميع التبعيات متوفرة")
        
        # إنشاء المجلدات
        print("\n📁 إنشاء المجلدات...")
        create_directories()
        
        # إعداد التسجيل
        setup_logging()
        
        # فحص النظام فقط
        if args.check:
            print("\n🔍 فحص النظام...")
            
            # فحص قاعدة البيانات
            try:
                from app.core.database import engine
                with engine.connect() as conn:
                    conn.execute("SELECT 1")
                print("✅ قاعدة البيانات: متصلة")
            except Exception as e:
                print(f"❌ قاعدة البيانات: خطأ - {e}")
            
            # فحص المنفذ
            if check_port_availability(args.port):
                print(f"✅ المنفذ {args.port}: متاح")
            else:
                print(f"❌ المنفذ {args.port}: مستخدم")
            
            print("\n✅ تم فحص النظام بنجاح")
            return
        
        # تهيئة قاعدة البيانات فقط
        if args.init_db:
            print("\n🗄️ تهيئة قاعدة البيانات...")
            from app.core.database import init_db
            init_db()
            print("✅ تم تهيئة قاعدة البيانات بنجاح")
            return
        
        # فحص المنفذ
        if not check_port_availability(args.port):
            print(f"❌ المنفذ {args.port} مستخدم بالفعل")
            print("يرجى استخدام منفذ آخر أو إيقاف التطبيق الذي يستخدم هذا المنفذ")
            sys.exit(1)
        
        # طباعة معلومات التطبيق
        print_banner()
        
        # إعداد خيارات Uvicorn
        uvicorn_config = {
            "app": "app.main:app",
            "host": args.host,
            "port": args.port,
            "log_level": args.log_level,
            "access_log": settings.DEBUG,
            "reload": args.reload or settings.DEBUG,
            "workers": 1 if (args.reload or settings.DEBUG) else args.workers,
        }
        
        # إضافة SSL إذا تم تحديده
        if args.ssl_keyfile and args.ssl_certfile:
            uvicorn_config.update({
                "ssl_keyfile": args.ssl_keyfile,
                "ssl_certfile": args.ssl_certfile
            })
            print(f"🔒 تم تفعيل SSL")
        
        # تشغيل الخادم
        print(f"\n🚀 بدء تشغيل الخادم...")
        print(f"📡 الاستماع على: {args.host}:{args.port}")
        print(f"🔧 وضع التطوير: {'مُفعل' if uvicorn_config['reload'] else 'مُعطل'}")
        print(f"👥 عدد العمليات: {uvicorn_config['workers']}")
        print("\n" + "="*60)
        print("للوصول للنظام، افتح:")
        print(f"  🌐 لوحة التحكم: http://{args.host}:{args.port}/")
        print(f"  📚 وثائق API: http://{args.host}:{args.port}/api/docs")
        print("="*60 + "\n")
        
        # تشغيل Uvicorn
        uvicorn.run(**uvicorn_config)
        
    except KeyboardInterrupt:
        print("\n\n⏹️ تم إيقاف الخادم بواسطة المستخدم")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ خطأ في تشغيل الخادم: {e}")
        import traceback
        if settings.DEBUG:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()