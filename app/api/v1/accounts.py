"""
API endpoints لإدارة الحسابات
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.security import APIKeyAuth
from app.models.account import Account
from app.models.api_key import APIKey

router = APIRouter()
api_key_auth = APIKeyAuth()


class AccountCreate(BaseModel):
    name: str = Field(..., description="اسم الحساب")
    token: str = Field(..., description="JWT Token")
    device_id: str = Field(..., description="معرف الجهاز")
    player_id: str = Field(..., description="معرف المشغل")
    user_agent: Optional[str] = Field(None, description="User Agent")
    rate_limit: int = Field(default=50, description="حد الطلبات في الساعة")
    country: str = Field(default="IQ", description="البلد")
    locale: str = Field(default="ar", description="اللغة")
    notes: Optional[str] = Field(None, description="ملاحظات")


class AccountUpdate(BaseModel):
    name: Optional[str] = None
    token: Optional[str] = None
    device_id: Optional[str] = None
    player_id: Optional[str] = None
    user_agent: Optional[str] = None
    rate_limit: Optional[int] = None
    country: Optional[str] = None
    locale: Optional[str] = None
    is_active: Optional[bool] = None
    is_banned: Optional[bool] = None
    ban_reason: Optional[str] = None
    notes: Optional[str] = None


class AccountResponse(BaseModel):
    id: int
    name: str
    device_id: str
    player_id: str
    request_count: int
    successful_requests: int
    failed_requests: int
    rate_limit: int
    current_hour_requests: int
    is_active: bool
    is_banned: bool
    country: str
    locale: str
    success_rate: float
    remaining_requests: int


@router.get("/accounts", response_model=List[AccountResponse])
async def get_accounts(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth)
):
    """
    الحصول على قائمة الحسابات
    """
    query = db.query(Account)
    
    if active_only:
        query = query.filter(Account.is_active == True, Account.is_banned == False)
    
    accounts = query.offset(skip).limit(limit).all()
    
    return [
        AccountResponse(
            **account.to_dict(),
            success_rate=account.success_rate,
            remaining_requests=account.remaining_requests
        )
        for account in accounts
    ]


@router.get("/accounts/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: int,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth)
):
    """
    الحصول على حساب محدد
    """
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    return AccountResponse(
        **account.to_dict(),
        success_rate=account.success_rate,
        remaining_requests=account.remaining_requests
    )


@router.post("/accounts", response_model=AccountResponse)
async def create_account(
    account_data: AccountCreate,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth)
):
    """
    إنشاء حساب جديد
    """
    # التحقق من عدم تكرار device_id
    existing_account = db.query(Account).filter(
        Account.device_id == account_data.device_id
    ).first()
    
    if existing_account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account with this device_id already exists"
        )
    
    account = Account(**account_data.dict())
    db.add(account)
    db.commit()
    db.refresh(account)
    
    return AccountResponse(
        **account.to_dict(),
        success_rate=account.success_rate,
        remaining_requests=account.remaining_requests
    )


@router.put("/accounts/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: int,
    account_data: AccountUpdate,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth)
):
    """
    تحديث حساب موجود
    """
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # تحديث الحقول المرسلة فقط
    for field, value in account_data.dict(exclude_unset=True).items():
        setattr(account, field, value)
    
    db.commit()
    db.refresh(account)
    
    return AccountResponse(
        **account.to_dict(),
        success_rate=account.success_rate,
        remaining_requests=account.remaining_requests
    )


@router.delete("/accounts/{account_id}")
async def delete_account(
    account_id: int,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth)
):
    """
    حذف حساب
    """
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    db.delete(account)
    db.commit()
    
    return {"message": "Account deleted successfully"}


@router.post("/accounts/{account_id}/toggle")
async def toggle_account_status(
    account_id: int,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth)
):
    """
    تفعيل/إلغاء تفعيل الحساب
    """
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    account.is_active = not account.is_active
    db.commit()
    
    return {
        "message": f"Account {'activated' if account.is_active else 'deactivated'}",
        "is_active": account.is_active
    }


@router.post("/accounts/{account_id}/ban")
async def ban_account(
    account_id: int,
    reason: str,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth)
):
    """
    حظر حساب
    """
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    account.is_banned = True
    account.ban_reason = reason
    db.commit()
    
    return {"message": "Account banned successfully"}


@router.post("/accounts/{account_id}/unban")
async def unban_account(
    account_id: int,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth)
):
    """
    إلغاء حظر حساب
    """
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    account.is_banned = False
    account.ban_reason = None
    db.commit()
    
    return {"message": "Account unbanned successfully"}


@router.get("/accounts/stats/summary")
async def get_accounts_summary(
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth)
):
    """
    ملخص إحصائيات الحسابات
    """
    total_accounts = db.query(Account).count()
    active_accounts = db.query(Account).filter(Account.is_active == True).count()
    banned_accounts = db.query(Account).filter(Account.is_banned == True).count()
    
    # الحسابات المتاحة للاستخدام
    available_accounts = db.query(Account).filter(
        Account.is_active == True,
        Account.is_banned == False
    ).all()
    
    available_count = len([acc for acc in available_accounts if acc.can_make_request()])
    
    return {
        "total_accounts": total_accounts,
        "active_accounts": active_accounts,
        "banned_accounts": banned_accounts,
        "available_accounts": available_count,
        "usage_stats": {
            "total_requests": sum(acc.request_count for acc in available_accounts),
            "successful_requests": sum(acc.successful_requests for acc in available_accounts),
            "failed_requests": sum(acc.failed_requests for acc in available_accounts)
        }
    }