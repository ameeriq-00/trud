"""
التطبيق الرئيسي - FastAPI App
"""
from fastapi import FastAPI, Request, Depends, HTTPException, status, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uvicorn

from app.core.config import settings
from app.core.database import get_db, init_db
from app.core.security import check_admin_credentials, create_access_token

# استيراد الـ routers
from app.api.v1 import search, accounts, proxies, sessions

# إنشاء التطبيق
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="نظام بروكسي غير رسمي لـ HelloCallers API مع واجهة إدارية",
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None
)

# إضافة CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ملفات ثابتة وقوالب
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# تضمين API routes
app.include_router(search.router, prefix="/api/v1", tags=["بحث"])
app.include_router(accounts.router, prefix="/api/v1", tags=["حسابات"])
app.include_router(proxies.router, prefix="/api/v1", tags=["بروكسيات"])
app.include_router(sessions.router, prefix="/api/v1", tags=["جلسات"])


@app.on_event("startup")
async def startup_event():
    """أحداث بدء التشغيل"""
    print(f"🚀 بدء تشغيل {settings.PROJECT_NAME} v{settings.VERSION}")
    
    # إنشاء قاعدة البيانات والجداول
    init_db()
    print("✅ تم إنشاء قاعدة البيانات")


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """الصفحة الرئيسية - لوحة التحكم"""
    from app.models.account import Account
    from app.models.proxy import Proxy
    from app.models.session import Session as SessionModel
    from app.models.api_key import APIKey
    from sqlalchemy import func
    
    # جمع الإحصائيات
    total_accounts = db.query(Account).count()
    active_accounts = db.query(Account).filter(Account.is_active == True).count()
    total_proxies = db.query(Proxy).count()
    working_proxies = db.query(Proxy).filter(Proxy.is_working == True).count()
    total_sessions = db.query(SessionModel).count()
    successful_sessions = db.query(SessionModel).filter(SessionModel.status == "success").count()
    total_api_keys = db.query(APIKey).count()
    active_api_keys = db.query(APIKey).filter(APIKey.is_active == True).count()
    
    # آخر الجلسات
    recent_sessions = db.query(SessionModel).order_by(SessionModel.created_at.desc()).limit(10).all()
    
    stats = {
        "accounts": {"total": total_accounts, "active": active_accounts},
        "proxies": {"total": total_proxies, "working": working_proxies},
        "sessions": {"total": total_sessions, "successful": successful_sessions},
        "api_keys": {"total": total_api_keys, "active": active_api_keys},
        "recent_sessions": [session.to_dict() for session in recent_sessions]
    }
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "stats": stats,
        "app_name": settings.PROJECT_NAME,
        "version": settings.VERSION
    })


@app.get("/accounts", response_class=HTMLResponse)
async def accounts_page(request: Request, db: Session = Depends(get_db)):
    """صفحة إدارة الحسابات"""
    from app.models.account import Account
    
    accounts = db.query(Account).order_by(Account.created_at.desc()).all()
    
    return templates.TemplateResponse("accounts.html", {
        "request": request,
        "accounts": [account.to_dict() for account in accounts],
        "app_name": settings.PROJECT_NAME
    })


@app.get("/proxies", response_class=HTMLResponse)
async def proxies_page(request: Request, db: Session = Depends(get_db)):
    """صفحة إدارة البروكسيات"""
    from app.models.proxy import Proxy
    
    proxies = db.query(Proxy).order_by(Proxy.created_at.desc()).all()
    
    return templates.TemplateResponse("proxies.html", {
        "request": request,
        "proxies": [proxy.to_dict() for proxy in proxies],
        "app_name": settings.PROJECT_NAME
    })


@app.get("/sessions", response_class=HTMLResponse)
async def sessions_page(request: Request, db: Session = Depends(get_db)):
    """صفحة مراقبة الجلسات"""
    from app.models.session import Session as SessionModel
    
    sessions = db.query(SessionModel).order_by(SessionModel.created_at.desc()).limit(100).all()
    
    return templates.TemplateResponse("sessions.html", {
        "request": request,
        "sessions": [session.to_dict() for session in sessions],
        "app_name": settings.PROJECT_NAME
    })


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """صفحة تسجيل الدخول"""
    return templates.TemplateResponse("login.html", {
        "request": request,
        "app_name": settings.PROJECT_NAME
    })


@app.post("/login")
async def login(request: Request):
    """تسجيل الدخول"""
    try:
        # قراءة البيانات من النموذج
        form_data = await request.form()
        username = form_data.get("username")
        password = form_data.get("password")
        
        # التحقق من وجود البيانات
        if not username or not password:
            return templates.TemplateResponse("login.html", {
                "request": request,
                "error": "يرجى إدخال اسم المستخدم وكلمة المرور",
                "app_name": settings.PROJECT_NAME
            })
        
        # التحقق من صحة البيانات
        if check_admin_credentials(username, password):
            # إنشاء token وإعادة توجيه
            token = create_access_token({"sub": username, "role": "admin"})
            response = RedirectResponse(url="/", status_code=303)
            response.set_cookie(key="access_token", value=f"Bearer {token}", httponly=True)
            return response
        else:
            return templates.TemplateResponse("login.html", {
                "request": request,
                "error": "اسم المستخدم أو كلمة المرور غير صحيحة",
                "app_name": settings.PROJECT_NAME
            })
    
    except Exception as e:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": f"خطأ في تسجيل الدخول: {str(e)}",
            "app_name": settings.PROJECT_NAME
        })


@app.get("/logout")
async def logout():
    """تسجيل الخروج"""
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key="access_token")
    return response

@app.get("/search-test", response_class=HTMLResponse)
async def search_test_page(request: Request):
    """صفحة اختبار البحث"""
    return templates.TemplateResponse("search_test.html", {
        "request": request,
        "app_name": settings.PROJECT_NAME
    })


@app.get("/", response_class=HTMLResponse)

@app.get("/health")
async def health_check():
    """فحص صحة النظام"""
    from datetime import datetime
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.VERSION,
        "environment": "development" if settings.DEBUG else "production"
    }


@app.get("/api/status")
async def api_status(db: Session = Depends(get_db)):
    """حالة API"""
    from app.models.account import Account
    from app.models.proxy import Proxy
    
    available_accounts = db.query(Account).filter(
        Account.is_active == True,
        Account.is_banned == False
    ).count()
    
    working_proxies = db.query(Proxy).filter(
        Proxy.is_active == True,
        Proxy.is_working == True
    ).count()
    
    return {
        "api_status": "operational",
        "available_accounts": available_accounts,
        "working_proxies": working_proxies,
        "timestamp": "2025-08-18T01:24:00Z"
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        access_log=True
    )