#!/usr/bin/env python3
"""
ملف تشغيل المشروع
"""
import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    print(f"🚀 تشغيل {settings.PROJECT_NAME}")
    print(f"📍 العنوان: http://{settings.HOST}:{settings.PORT}")
    print(f"📖 وثائق API: http://{settings.HOST}:{settings.PORT}/api/docs")
    print(f"🔑 API Key الافتراضي: trud-admin-key-12345")
    print("=" * 50)
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        access_log=True,
        log_level=settings.LOG_LEVEL.lower()
    )