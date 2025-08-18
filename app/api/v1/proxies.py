"""
API endpoints لإدارة البروكسيات
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.security import APIKeyAuth
from app.models.proxy import Proxy
from app.models.api_key import APIKey
from app.services.proxy_manager import ProxyManager

router = APIRouter()
api_key_auth = APIKeyAuth()


class ProxyCreate(BaseModel):
    name: str = Field(..., description="اسم البروكسي")
    host: str = Field(..., description="عنوان الخادم")
    port: int = Field(..., description="المنفذ", ge=1, le=65535)
    username: Optional[str] = Field(None, description="اسم المستخدم")
    password: Optional[str] = Field(None, description="كلمة المرور")
    proxy_type: str = Field(default="http", description="نوع البروكسي")
    country: Optional[str] = Field(None, description="البلد")
    city: Optional[str] = Field(None, description="المدينة")
    timeout: int = Field(default=30, description="مهلة الاتصال بالثواني")
    max_concurrent_requests: int = Field(default=5, description="الحد الأقصى للطلبات المتزامنة")
    notes: Optional[str] = Field(None, description="ملاحظات")


class ProxyUpdate(BaseModel):
    name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    proxy_type: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    timeout: Optional[int] = None
    max_concurrent_requests: Optional[int] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class ProxyResponse(BaseModel):
    id: int
    name: str
    host: str
    port: int
    username: Optional[str]
    proxy_type: str
    country: Optional[str]
    city: Optional[str]
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    is_active: bool
    is_working: bool
    status_message: Optional[str]
    success_rate: float


class ProxyTestResult(BaseModel):
    proxy_id: int
    proxy_name: str
    is_working: bool
    response_time: float
    ip_address: Optional[str]
    error_message: Optional[str]
    test_url: Optional[str]


@router.get("/proxies", response_model=List[ProxyResponse])
async def get_proxies(
    skip: int = 0,
    limit: int = 100,
    working_only: bool = False,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth)
):
    """
    الحصول على قائمة البروكسيات
    """
    query = db.query(Proxy)
    
    if working_only:
        query = query.filter(Proxy.is_active == True, Proxy.is_working == True)
    
    proxies = query.offset(skip).limit(limit).all()
    
    return [
        ProxyResponse(
            **proxy.to_dict(),
            success_rate=proxy.success_rate
        )
        for proxy in proxies
    ]


@router.get("/proxies/{proxy_id}", response_model=ProxyResponse)
async def get_proxy(
    proxy_id: int,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth)
):
    """
    الحصول على بروكسي محدد
    """
    proxy = db.query(Proxy).filter(Proxy.id == proxy_id).first()
    if not proxy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proxy not found"
        )
    
    return ProxyResponse(
        **proxy.to_dict(),
        success_rate=proxy.success_rate
    )


@router.post("/proxies", response_model=ProxyResponse)
async def create_proxy(
    proxy_data: ProxyCreate,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth)
):
    """
    إنشاء بروكسي جديد
    """
    # التحقق من عدم تكرار البروكسي
    existing_proxy = db.query(Proxy).filter(
        Proxy.host == proxy_data.host,
        Proxy.port == proxy_data.port
    ).first()
    
    if existing_proxy:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Proxy with this host and port already exists"
        )
    
    proxy = Proxy(**proxy_data.dict())
    db.add(proxy)
    db.commit()
    db.refresh(proxy)
    
    return ProxyResponse(
        **proxy.to_dict(),
        success_rate=proxy.success_rate
    )


@router.put("/proxies/{proxy_id}", response_model=ProxyResponse)
async def update_proxy(
    proxy_id: int,
    proxy_data: ProxyUpdate,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth)
):
    """
    تحديث بروكسي موجود
    """
    proxy = db.query(Proxy).filter(Proxy.id == proxy_id).first()
    if not proxy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proxy not found"
        )
    
    # تحديث الحقول المرسلة فقط
    for field, value in proxy_data.dict(exclude_unset=True).items():
        setattr(proxy, field, value)
    
    db.commit()
    db.refresh(proxy)
    
    return ProxyResponse(
        **proxy.to_dict(),
        success_rate=proxy.success_rate
    )


@router.delete("/proxies/{proxy_id}")
async def delete_proxy(
    proxy_id: int,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth)
):
    """
    حذف بروكسي
    """
    proxy = db.query(Proxy).filter(Proxy.id == proxy_id).first()
    if not proxy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proxy not found"
        )
    
    db.delete(proxy)
    db.commit()
    
    return {"message": "Proxy deleted successfully"}


@router.post("/proxies/{proxy_id}/toggle")
async def toggle_proxy_status(
    proxy_id: int,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth)
):
    """
    تفعيل/إلغاء تفعيل البروكسي
    """
    proxy = db.query(Proxy).filter(Proxy.id == proxy_id).first()
    if not proxy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proxy not found"
        )
    
    proxy.is_active = not proxy.is_active
    db.commit()
    
    return {
        "message": f"Proxy {'activated' if proxy.is_active else 'deactivated'}",
        "is_active": proxy.is_active
    }


@router.post("/proxies/{proxy_id}/test", response_model=ProxyTestResult)
async def test_single_proxy(
    proxy_id: int,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth)
):
    """
    اختبار بروكسي واحد
    """
    proxy = db.query(Proxy).filter(Proxy.id == proxy_id).first()
    if not proxy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proxy not found"
        )
    
    proxy_manager = ProxyManager(db)
    test_result = await proxy_manager.test_proxy(proxy)
    
    return ProxyTestResult(**test_result)


@router.post("/proxies/test-all")
async def test_all_proxies(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth)
):
    """
    اختبار جميع البروكسيات
    """
    proxy_manager = ProxyManager(db)
    
    # تشغيل الاختبار في الخلفية
    background_tasks.add_task(proxy_manager.test_all_proxies)
    
    return {
        "message": "Proxy testing started in background",
        "status": "testing_started"
    }


@router.get("/proxies/test-all/results")
async def get_test_results(
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth)
):
    """
    الحصول على نتائج اختبار البروكسيات
    """
    proxy_manager = ProxyManager(db)
    results = await proxy_manager.test_all_proxies()
    
    return results


@router.get("/proxies/stats/summary")
async def get_proxies_summary(
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth)
):
    """
    ملخص إحصائيات البروكسيات
    """
    proxy_manager = ProxyManager(db)
    stats = proxy_manager.get_proxy_statistics()
    
    return stats


@router.post("/proxies/optimize")
async def optimize_proxies(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth)
):
    """
    تحسين البروكسيات (إيقاف البروكسيات السيئة، تحديث الإحصائيات)
    """
    proxy_manager = ProxyManager(db)
    
    # تشغيل التحسين في الخلفية
    optimization_result = proxy_manager.optimize_proxy_usage()
    
    return {
        "message": "Proxy optimization completed",
        "results": optimization_result
    }


@router.get("/proxies/working")
async def get_working_proxies(
    limit: Optional[int] = 10,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth)
):
    """
    الحصول على البروكسيات العاملة فقط
    """
    proxy_manager = ProxyManager(db)
    working_proxies = proxy_manager.get_working_proxies(limit=limit)
    
    return [
        ProxyResponse(
            **proxy.to_dict(),
            success_rate=proxy.success_rate
        )
        for proxy in working_proxies
    ]


@router.get("/proxies/best")
async def get_best_proxy(
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth)
):
    """
    الحصول على أفضل بروكسي متاح
    """
    proxy_manager = ProxyManager(db)
    best_proxy = proxy_manager.get_best_proxy()
    
    if not best_proxy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No working proxy available"
        )
    
    return ProxyResponse(
        **best_proxy.to_dict(),
        success_rate=best_proxy.success_rate
    )


@router.post("/proxies/health-check")
async def health_check_proxies(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth)
):
    """
    فحص صحة شامل لجميع البروكسيات
    """
    proxy_manager = ProxyManager(db)
    
    # تشغيل فحص الصحة في الخلفية
    health_results = await proxy_manager.health_check_all_proxies()
    
    return health_results


@router.post("/proxies/bulk-import")
async def bulk_import_proxies(
    proxies_data: List[ProxyCreate],
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth)
):
    """
    استيراد مجمع للبروكسيات
    """
    if len(proxies_data) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 50 proxies per bulk import"
        )
    
    created_proxies = []
    errors = []
    
    for proxy_data in proxies_data:
        try:
            # التحقق من عدم تكرار البروكسي
            existing_proxy = db.query(Proxy).filter(
                Proxy.host == proxy_data.host,
                Proxy.port == proxy_data.port
            ).first()
            
            if existing_proxy:
                errors.append(f"Proxy {proxy_data.host}:{proxy_data.port} already exists")
                continue
            
            proxy = Proxy(**proxy_data.dict())
            db.add(proxy)
            db.commit()
            db.refresh(proxy)
            created_proxies.append(proxy.to_dict())
            
        except Exception as e:
            errors.append(f"Failed to create proxy {proxy_data.host}:{proxy_data.port}: {str(e)}")
            db.rollback()
    
    return {
        "created_count": len(created_proxies),
        "error_count": len(errors),
        "created_proxies": created_proxies,
        "errors": errors
    }