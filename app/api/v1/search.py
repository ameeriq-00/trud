"""
API endpoints للبحث
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.security import APIKeyAuth
from app.services.hellocallers import HelloCallersService
from app.models.api_key import APIKey

router = APIRouter()
api_key_auth = APIKeyAuth()


class PhoneSearchRequest(BaseModel):
    phone_number: str = Field(..., description="رقم الهاتف للبحث عنه", example="+9647809394930")


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


class SearchResponse(BaseModel):
    success: bool
    phone_number: str
    session_id: str
    data: Dict[str, Any] = None
    error: str = None
    account_used: int = None
    proxy_used: int = None
    response_time: float


class BulkSearchResponse(BaseModel):
    total_searched: int
    successful_results: int
    failed_searches: int
    results: List[SearchResponse]
    errors: List[str]
    timestamp: str


@router.post("/search/phone", response_model=SearchResponse)
async def search_phone_number(
    request: PhoneSearchRequest,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth)
):
    """
    البحث عن رقم هاتف واحد
    
    يقوم هذا الـ endpoint بالبحث عن معلومات رقم هاتف واحد من خلال HelloCallers API
    """
    try:
        service = HelloCallersService(db)
        result = await service.search_single_phone(request.phone_number)
        
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
        "api_key_name": api_key.name
    }