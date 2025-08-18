"""
API endpoints لمراقبة الجلسات
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.security import APIKeyAuth
from app.models.session import Session as SessionModel
from app.models.account import Account
from app.models.proxy import Proxy
from app.models.api_key import APIKey

router = APIRouter()
api_key_auth = APIKeyAuth()


class SessionResponse(BaseModel):
    id: int
    session_id: str
    account_id: Optional[int]
    proxy_id: Optional[int]
    phone_number: str
    request_type: str
    status: str
    error_message: Optional[str]
    response_time: float
    contact_found: bool
    contact_name: Optional[str]
    carrier_name: Optional[str]
    country_code: Optional[str]
    is_spam: bool
    started_at: Optional[str]
    completed_at: Optional[str]
    created_at: Optional[str]


class SessionFilter(BaseModel):
    status: Optional[str] = None
    phone_number: Optional[str] = None
    account_id: Optional[int] = None
    proxy_id: Optional[int] = None
    contact_found: Optional[bool] = None
    is_spam: Optional[bool] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class SessionStatistics(BaseModel):
    total_sessions: int
    successful_sessions: int
    failed_sessions: int
    pending_sessions: int
    success_rate: float
    average_response_time: float
    contacts_found: int
    spam_numbers_detected: int
    unique_phone_numbers: int


@router.get("/sessions", response_model=List[SessionResponse])
async def get_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None, description="فلترة حسب الحالة"),
    phone_number: Optional[str] = Query(None, description="فلترة حسب رقم الهاتف"),
    account_id: Optional[int] = Query(None, description="فلترة حسب الحساب"),
    proxy_id: Optional[int] = Query(None, description="فلترة حسب البروكسي"),
    date_from: Optional[datetime] = Query(None, description="من تاريخ"),
    date_to: Optional[datetime] = Query(None, description="إلى تاريخ"),
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth)
):
    """
    الحصول على قائمة الجلسات مع إمكانية الفلترة
    """
    query = db.query(SessionModel)
    
    # تطبيق الفلاتر
    if status:
        query = query.filter(SessionModel.status == status)
    
    if phone_number:
        query = query.filter(SessionModel.phone_number.like(f"%{phone_number}%"))
    
    if account_id:
        query = query.filter(SessionModel.account_id == account_id)
    
    if proxy_id:
        query = query.filter(SessionModel.proxy_id == proxy_id)
    
    if date_from:
        query = query.filter(SessionModel.created_at >= date_from)
    
    if date_to:
        query = query.filter(SessionModel.created_at <= date_to)
    
    # ترتيب حسب الأحدث
    query = query.order_by(desc(SessionModel.created_at))
    
    sessions = query.offset(skip).limit(limit).all()
    
    return [SessionResponse(**session.to_dict()) for session in sessions]


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth)
):
    """
    الحصول على جلسة محددة
    """
    session = db.query(SessionModel).filter(
        SessionModel.session_id == session_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return SessionResponse(**session.to_dict())


@router.get("/sessions/stats/summary", response_model=SessionStatistics)
async def get_sessions_statistics(
    days: int = Query(7, ge=1, le=365, description="عدد الأيام للإحصائيات"),
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth)
):
    """
    إحصائيات الجلسات
    """
    # حساب التاريخ المطلوب
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # استعلام الجلسات في الفترة المحددة
    sessions_query = db.query(SessionModel).filter(
        SessionModel.created_at >= start_date
    )
    
    all_sessions = sessions_query.all()
    
    # حساب الإحصائيات
    total_sessions = len(all_sessions)
    successful_sessions = len([s for s in all_sessions if s.status == "success"])
    failed_sessions = len([s for s in all_sessions if s.status == "failed"])
    pending_sessions = len([s for s in all_sessions if s.status == "pending"])
    
    success_rate = (successful_sessions / total_sessions * 100) if total_sessions > 0 else 0
    
    # حساب متوسط وقت الاستجابة
    response_times = [s.response_time for s in all_sessions if s.response_time > 0]
    average_response_time = sum(response_times) / len(response_times) if response_times else 0
    
    # إحصائيات أخرى
    contacts_found = len([s for s in all_sessions if s.contact_found])
    spam_numbers = len([s for s in all_sessions if s.is_spam])
    unique_phones = len(set(s.phone_number for s in all_sessions))
    
    return SessionStatistics(
        total_sessions=total_sessions,
        successful_sessions=successful_sessions,
        failed_sessions=failed_sessions,
        pending_sessions=pending_sessions,
        success_rate=success_rate,
        average_response_time=average_response_time,
        contacts_found=contacts_found,
        spam_numbers_detected=spam_numbers,
        unique_phone_numbers=unique_phones
    )


@router.get("/sessions/stats/hourly")
async def get_hourly_statistics(
    hours: int = Query(24, ge=1, le=168, description="عدد الساعات"),
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth)
):
    """
    إحصائيات الجلسات بالساعة
    """
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    
    sessions = db.query(SessionModel).filter(
        SessionModel.created_at >= start_time
    ).all()
    
    # تجميع البيانات بالساعة
    hourly_stats = {}
    
    for session in sessions:
        if session.created_at:
            hour_key = session.created_at.strftime("%Y-%m-%d %H:00")
            
            if hour_key not in hourly_stats:
                hourly_stats[hour_key] = {
                    "hour": hour_key,
                    "total": 0,
                    "successful": 0,
                    "failed": 0,
                    "pending": 0
                }
            
            hourly_stats[hour_key]["total"] += 1
            
            if session.status == "success":
                hourly_stats[hour_key]["successful"] += 1
            elif session.status == "failed":
                hourly_stats[hour_key]["failed"] += 1
            elif session.status == "pending":
                hourly_stats[hour_key]["pending"] += 1
    
    # ترتيب حسب الوقت
    sorted_stats = sorted(hourly_stats.values(), key=lambda x: x["hour"])
    
    return {
        "period": f"Last {hours} hours",
        "hourly_data": sorted_stats
    }


@router.get("/sessions/stats/accounts")
async def get_account_usage_stats(
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth)
):
    """
    إحصائيات استخدام الحسابات
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # استعلام مع ربط الحسابات
    sessions = db.query(SessionModel, Account).join(
        Account, SessionModel.account_id == Account.id, isouter=True
    ).filter(
        SessionModel.created_at >= start_date
    ).all()
    
    account_stats = {}
    
    for session, account in sessions:
        account_id = session.account_id or "unknown"
        account_name = account.name if account else "Unknown Account"
        
        if account_id not in account_stats:
            account_stats[account_id] = {
                "account_id": account_id,
                "account_name": account_name,
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "success_rate": 0.0
            }
        
        account_stats[account_id]["total_requests"] += 1
        
        if session.status == "success":
            account_stats[account_id]["successful_requests"] += 1
        elif session.status == "failed":
            account_stats[account_id]["failed_requests"] += 1
    
    # حساب معدل النجاح
    for stats in account_stats.values():
        if stats["total_requests"] > 0:
            stats["success_rate"] = (
                stats["successful_requests"] / stats["total_requests"] * 100
            )
    
    return {
        "period": f"Last {days} days",
        "account_usage": list(account_stats.values())
    }


@router.get("/sessions/stats/proxies")
async def get_proxy_usage_stats(
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth)
):
    """
    إحصائيات استخدام البروكسيات
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # استعلام مع ربط البروكسيات
    sessions = db.query(SessionModel, Proxy).join(
        Proxy, SessionModel.proxy_id == Proxy.id, isouter=True
    ).filter(
        SessionModel.created_at >= start_date
    ).all()
    
    proxy_stats = {}
    
    for session, proxy in sessions:
        proxy_id = session.proxy_id or "direct"
        proxy_name = proxy.name if proxy else "Direct Connection"
        
        if proxy_id not in proxy_stats:
            proxy_stats[proxy_id] = {
                "proxy_id": proxy_id,
                "proxy_name": proxy_name,
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "success_rate": 0.0,
                "average_response_time": 0.0
            }
        
        proxy_stats[proxy_id]["total_requests"] += 1
        
        if session.status == "success":
            proxy_stats[proxy_id]["successful_requests"] += 1
        elif session.status == "failed":
            proxy_stats[proxy_id]["failed_requests"] += 1
        
        # متوسط وقت الاستجابة
        if session.response_time > 0:
            current_avg = proxy_stats[proxy_id]["average_response_time"]
            total_requests = proxy_stats[proxy_id]["total_requests"]
            proxy_stats[proxy_id]["average_response_time"] = (
                (current_avg * (total_requests - 1) + session.response_time) / total_requests
            )
    
    # حساب معدل النجاح
    for stats in proxy_stats.values():
        if stats["total_requests"] > 0:
            stats["success_rate"] = (
                stats["successful_requests"] / stats["total_requests"] * 100
            )
    
    return {
        "period": f"Last {days} days",
        "proxy_usage": list(proxy_stats.values())
    }


@router.get("/sessions/phone-numbers/top")
async def get_top_searched_numbers(
    limit: int = Query(20, ge=1, le=100),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth)
):
    """
    أكثر الأرقام بحثاً
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    sessions = db.query(SessionModel).filter(
        SessionModel.created_at >= start_date
    ).all()
    
    # تجميع الأرقام وعدد البحث
    phone_counts = {}
    
    for session in sessions:
        phone = session.phone_number
        if phone not in phone_counts:
            phone_counts[phone] = {
                "phone_number": phone,
                "search_count": 0,
                "contact_name": session.contact_name,
                "carrier_name": session.carrier_name,
                "is_spam": session.is_spam,
                "last_searched": session.created_at
            }
        
        phone_counts[phone]["search_count"] += 1
        
        # تحديث آخر بحث
        if session.created_at > phone_counts[phone]["last_searched"]:
            phone_counts[phone]["last_searched"] = session.created_at
            phone_counts[phone]["contact_name"] = session.contact_name
            phone_counts[phone]["carrier_name"] = session.carrier_name
            phone_counts[phone]["is_spam"] = session.is_spam
    
    # ترتيب حسب عدد البحث
    top_numbers = sorted(
        phone_counts.values(),
        key=lambda x: x["search_count"],
        reverse=True
    )[:limit]
    
    # تحويل التواريخ إلى نص
    for item in top_numbers:
        if item["last_searched"]:
            item["last_searched"] = item["last_searched"].isoformat()
    
    return {
        "period": f"Last {days} days",
        "top_searched_numbers": top_numbers
    }


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth)
):
    """
    حذف جلسة محددة
    """
    session = db.query(SessionModel).filter(
        SessionModel.session_id == session_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    db.delete(session)
    db.commit()
    
    return {"message": "Session deleted successfully"}


@router.delete("/sessions/cleanup")
async def cleanup_old_sessions(
    days: int = Query(30, ge=1, le=365, description="حذف الجلسات الأقدم من"),
    status_filter: Optional[str] = Query(None, description="حذف حسب الحالة فقط"),
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth)
):
    """
    تنظيف الجلسات القديمة
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    query = db.query(SessionModel).filter(
        SessionModel.created_at < cutoff_date
    )
    
    if status_filter:
        query = query.filter(SessionModel.status == status_filter)
    
    deleted_count = query.count()
    query.delete(synchronize_session=False)
    db.commit()
    
    return {
        "message": f"Cleaned up {deleted_count} old sessions",
        "deleted_count": deleted_count,
        "cutoff_date": cutoff_date.isoformat()
    }


@router.get("/sessions/export")
async def export_sessions(
    format: str = Query("json", regex="^(json|csv)$"),
    days: int = Query(7, ge=1, le=365),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth)
):
    """
    تصدير الجلسات
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    query = db.query(SessionModel).filter(
        SessionModel.created_at >= start_date
    )
    
    if status:
        query = query.filter(SessionModel.status == status)
    
    sessions = query.order_by(desc(SessionModel.created_at)).all()
    
    # تحويل إلى قائمة من القواميس
    sessions_data = []
    for session in sessions:
        session_dict = session.to_dict()
        sessions_data.append(session_dict)
    
    if format == "json":
        return {
            "export_format": "json",
            "export_date": datetime.utcnow().isoformat(),
            "period": f"Last {days} days",
            "total_sessions": len(sessions_data),
            "sessions": sessions_data
        }
    
    elif format == "csv":
        # تحويل إلى CSV
        import io
        import csv
        from fastapi.responses import StreamingResponse
        
        output = io.StringIO()
        
        if sessions_data:
            writer = csv.DictWriter(output, fieldnames=sessions_data[0].keys())
            writer.writeheader()
            writer.writerows(sessions_data)
        
        output.seek(0)
        
        def iter_csv():
            yield output.getvalue()
        
        return StreamingResponse(
            iter_csv(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=sessions_export.csv"}
        )


@router.get("/sessions/realtime/status")
async def get_realtime_status(
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth)
):
    """
    حالة الجلسات في الوقت الفعلي
    """
    # الجلسات في آخر 5 دقائق
    recent_time = datetime.utcnow() - timedelta(minutes=5)
    
    recent_sessions = db.query(SessionModel).filter(
        SessionModel.created_at >= recent_time
    ).all()
    
    # الجلسات النشطة (قيد التنفيذ)
    active_sessions = db.query(SessionModel).filter(
        SessionModel.status == "pending"
    ).count()
    
    # إحصائيات سريعة
    recent_successful = len([s for s in recent_sessions if s.status == "success"])
    recent_failed = len([s for s in recent_sessions if s.status == "failed"])
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "active_sessions": active_sessions,
        "recent_activity": {
            "last_5_minutes": len(recent_sessions),
            "successful": recent_successful,
            "failed": recent_failed
        },
        "system_status": "operational" if active_sessions < 100 else "busy"
    }


@router.get("/sessions/analysis/patterns")
async def analyze_search_patterns(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(api_key_auth)
):
    """
    تحليل أنماط البحث
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    sessions = db.query(SessionModel).filter(
        SessionModel.created_at >= start_date
    ).all()
    
    # تحليل أنماط مختلفة
    patterns = {
        "hourly_distribution": {},
        "daily_distribution": {},
        "country_codes": {},
        "carriers": {},
        "spam_ratio": 0.0,
        "success_by_hour": {},
        "response_time_by_hour": {}
    }
    
    total_sessions = len(sessions)
    spam_count = 0
    
    for session in sessions:
        if not session.created_at:
            continue
        
        # التوزيع بالساعة
        hour = session.created_at.hour
        patterns["hourly_distribution"][hour] = patterns["hourly_distribution"].get(hour, 0) + 1
        
        # التوزيع اليومي
        day = session.created_at.strftime("%A")
        patterns["daily_distribution"][day] = patterns["daily_distribution"].get(day, 0) + 1
        
        # رموز البلدان
        if session.country_code:
            patterns["country_codes"][session.country_code] = patterns["country_codes"].get(session.country_code, 0) + 1
        
        # المشغلين
        if session.carrier_name:
            patterns["carriers"][session.carrier_name] = patterns["carriers"].get(session.carrier_name, 0) + 1
        
        # حساب الرقم المزعج
        if session.is_spam:
            spam_count += 1
        
        # معدل النجاح بالساعة
        if hour not in patterns["success_by_hour"]:
            patterns["success_by_hour"][hour] = {"total": 0, "successful": 0}
        
        patterns["success_by_hour"][hour]["total"] += 1
        if session.status == "success":
            patterns["success_by_hour"][hour]["successful"] += 1
        
        # وقت الاستجابة بالساعة
        if session.response_time > 0:
            if hour not in patterns["response_time_by_hour"]:
                patterns["response_time_by_hour"][hour] = []
            patterns["response_time_by_hour"][hour].append(session.response_time)
    
    # حساب نسبة الأرقام المزعجة
    patterns["spam_ratio"] = (spam_count / total_sessions * 100) if total_sessions > 0 else 0
    
    # حساب متوسط أوقات الاستجابة بالساعة
    for hour, times in patterns["response_time_by_hour"].items():
        patterns["response_time_by_hour"][hour] = sum(times) / len(times)
    
    # حساب معدل النجاح بالساعة
    for hour, data in patterns["success_by_hour"].items():
        if data["total"] > 0:
            patterns["success_by_hour"][hour] = (data["successful"] / data["total"]) * 100
        else:
            patterns["success_by_hour"][hour] = 0
    
    return {
        "analysis_period": f"Last {days} days",
        "total_sessions_analyzed": total_sessions,
        "patterns": patterns,
        "insights": _generate_insights(patterns, total_sessions)
    }


def _generate_insights(patterns: dict, total_sessions: int) -> List[str]:
    """إنشاء رؤى من تحليل الأنماط"""
    insights = []
    
    # أكثر الساعات نشاطاً
    if patterns["hourly_distribution"]:
        busiest_hour = max(patterns["hourly_distribution"], key=patterns["hourly_distribution"].get)
        insights.append(f"أكثر الساعات نشاطاً: {busiest_hour}:00")
    
    # نسبة الأرقام المزعجة
    spam_ratio = patterns["spam_ratio"]
    if spam_ratio > 20:
        insights.append(f"نسبة عالية من الأرقام المزعجة: {spam_ratio:.1f}%")
    elif spam_ratio < 5:
        insights.append(f"نسبة منخفضة من الأرقام المزعجة: {spam_ratio:.1f}%")
    
    # أكثر المشغلين بحثاً
    if patterns["carriers"]:
        top_carrier = max(patterns["carriers"], key=patterns["carriers"].get)
        insights.append(f"أكثر المشغلين بحثاً: {top_carrier}")
    
    return insights