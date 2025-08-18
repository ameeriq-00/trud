"""
API endpoints للبحث - محسن
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.security import APIKeyAuth
from app.services.hellocallers import HelloCallersServiceAPK as HelloCallersService
from app.models.api_key import APIKey

router = APIRouter()
api_key_auth = APIKeyAuth()


class PhoneSearchRequest(BaseModel):
    phone_number: str = Field(..., description="رقم الهاتف للبحث عنه", example="+9647809394930")
    account_id: Optional[int] = Field(None, description="معرف الحساب المحدد")
    proxy_id: Optional[int] = Field(None, description="معرف البروكسي المحدد")
    debug_mode: bool = Field(False, description="تفعيل وضع التصحيح")


class BulkSearchRequest(BaseModel):
    phone_numbers: List[str] = Field(
        ..., 
        description="قائمة أرقام الهواتف للبحث عنها",
        max_items=100,
        example=["+9647809394930", "+9647801234567"]
    )
    max_concurrent: int = Field(
        default=5, 
        description="الحد الأقصى للطلبات المتزامنة",
        ge=1, 
        le=10
    )
    delay_between_requests: float = Field(
        default=1.0,
        description="التأخير بين الطلبات بالثواني",
        ge=0.1,
        le=10.0
    )
    account_id: Optional[int] = Field(None, description="معرف الحساب المحدد")
    proxy_id: Optional[int] = Field(None, description="معرف البروكسي المحدد")


class SearchResponse(BaseModel):
    success: bool
    phone_number: str
    session_id: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    account_used: Optional[int] = None
    proxy_used: Optional[int] = None
    response_time: float


class BulkSearchResponse(BaseModel):
    total_searched: int
    successful_results: int
    failed_searches: int
    results: List[SearchResponse]
    errors: List[str]
    timestamp: str


class TestAccountRequest(BaseModel):
    account_id: int = Field(..., description="معرف الحساب للاختبار")


class TestAccountResponse(BaseModel):
    success: bool
    account_id: int
    status: Optional[str] = None
    error: Optional[str] = None
    response_time: Optional[float] = None


@router.post("/search/phone", response_model=SearchResponse)
async def search_phone_number(
    request: PhoneSearchRequest,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth)
):
    """
    البحث عن رقم هاتف واحد
    
    يقوم هذا الـ endpoint بالبحث عن معلومات رقم هاتف واحد من خلال HelloCallers API
    مع إمكانية تحديد الحساب والبروكسي وتفعيل وضع التصحيح
    """
    try:
        service = HelloCallersService(db)
        result = await service.search_single_phone(
            phone_number=request.phone_number,
            account_id=request.account_id,
            proxy_id=request.proxy_id,
            debug_mode=request.debug_mode
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"]
            )
        
        return SearchResponse(**result)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching phone number: {str(e)}"
        )


@router.post("/search/bulk", response_model=BulkSearchResponse)
async def bulk_search_phone_numbers(
    request: BulkSearchRequest,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth)
):
    """
    البحث المجمع عن عدة أرقام هواتف
    
    يقوم هذا الـ endpoint بالبحث عن معلومات عدة أرقام هواتف بطريقة متوازية
    مع إمكانية التحكم في عدد الطلبات المتزامنة والتأخير بينها
    """
    try:
        service = HelloCallersService(db)
        result = await service.bulk_search_phones(
            phone_numbers=request.phone_numbers,
            max_concurrent=request.max_concurrent,
            delay_between_requests=request.delay_between_requests
        )
        
        return BulkSearchResponse(**result)
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in bulk search: {str(e)}"
        )


@router.post("/search/test-account", response_model=TestAccountResponse)
async def test_account(
    request: TestAccountRequest,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth)
):
    """
    اختبار حساب معين للتأكد من عمله
    """
    try:
        service = HelloCallersService(db)
        result = await service.test_account(request.account_id)
        
        return TestAccountResponse(**result)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error testing account: {str(e)}"
        )


@router.get("/search/account-history/{account_id}")
async def get_account_history(
    account_id: int,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth)
):
    """
    جلب تاريخ البحث لحساب معين
    """
    try:
        service = HelloCallersService(db)
        result = await service.get_account_history(account_id)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"]
            )
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting account history: {str(e)}"
        )


@router.get("/search/statistics")
async def get_search_statistics(
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth)
):
    """
    إحصائيات الخدمة العامة
    """
    try:
        service = HelloCallersService(db)
        stats = service.get_service_statistics()
        
        return {
            "message": "Service statistics",
            "data": stats,
            "api_key_name": api_key.name
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting statistics: {str(e)}"
        )


@router.get("/search/test")
async def test_search_endpoint(
    api_key: APIKey = Depends(api_key_auth)
):
    """
    اختبار API للتأكد من العمل
    """
    return {
        "message": "Search API is working",
        "timestamp": "2025-08-18T01:24:00Z",
        "api_key_name": api_key.name,
        "endpoints": [
            "POST /search/phone - البحث عن رقم واحد",
            "POST /search/bulk - البحث المجمع", 
            "POST /search/test-account - اختبار حساب",
            "GET /search/account-history/{id} - تاريخ الحساب",
            "GET /search/statistics - الإحصائيات"
        ]
    }


@router.get("/search/debug/payload/{phone_number}")
async def debug_payload_generation(
    phone_number: str,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth)
):
    """
    تصحيح إنشاء الـ payload - للتطوير فقط
    """
    try:
        from app.utils.encryption import HelloCallersEncryption
        
        encryption = HelloCallersEncryption()
        
        # إنشاء عدة payloads للمقارنة
        payloads = []
        for i in range(3):
            payload = encryption.encrypt_phone_search(phone_number)
            analysis = encryption.debug_payload_analysis(payload)
            payloads.append({
                "iteration": i + 1,
                "payload": payload,
                "analysis": analysis
            })
        
        return {
            "phone_number": phone_number,
            "generated_payloads": payloads,
            "har_examples": encryption.har_examples,
            "pattern_analysis": encryption.pattern_analysis
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in debug: {str(e)}"
        )