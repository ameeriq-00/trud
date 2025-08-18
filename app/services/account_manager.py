"""
خدمة إدارة الحسابات
"""
import random
import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.account import Account
from app.core.config import settings


class AccountManager:
    """مدير الحسابات - إدارة شاملة للحسابات"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_available_accounts(self, limit: Optional[int] = None) -> List[Account]:
        """الحصول على الحسابات المتاحة للاستخدام"""
        query = self.db.query(Account).filter(
            and_(
                Account.is_active == True,
                Account.is_banned == False
            )
        )
        
        accounts = query.all()
        
        # فلترة الحسابات التي يمكنها إجراء طلبات
        available_accounts = []
        for account in accounts:
            if account.can_make_request():
                available_accounts.append(account)
        
        # ترتيب حسب عدد الطلبات المتبقية (الأكثر أولوية)
        available_accounts.sort(key=lambda x: x.remaining_requests, reverse=True)
        
        if limit:
            return available_accounts[:limit]
        
        return available_accounts
    
    def get_best_account(self) -> Optional[Account]:
        """الحصول على أفضل حساب متاح"""
        available_accounts = self.get_available_accounts(limit=10)
        
        if not available_accounts:
            return None
        
        # اختيار أفضل حساب بناءً على عدة معايير
        best_account = None
        best_score = -1
        
        for account in available_accounts:
            # حساب نقاط التقييم
            score = self._calculate_account_score(account)
            
            if score > best_score:
                best_score = score
                best_account = account
        
        return best_account
    
    def _calculate_account_score(self, account: Account) -> float:
        """حساب نقاط تقييم الحساب"""
        score = 0.0
        
        # معدل النجاح (50% من النقاط)
        success_rate = account.success_rate
        score += (success_rate / 100) * 50
        
        # الطلبات المتبقية (30% من النقاط)
        remaining_ratio = account.remaining_requests / account.rate_limit
        score += remaining_ratio * 30
        
        # عكس آخر استخدام (20% من النقاط)
        if account.last_used:
            time_since_last_use = datetime.utcnow() - account.last_used
            hours_since_use = time_since_last_use.total_seconds() / 3600
            # كلما كان آخر استخدام أبعد، كلما كانت النقاط أعلى
            score += min(hours_since_use * 2, 20)
        else:
            score += 20  # حساب جديد لم يستخدم بعد
        
        return score
    
    def distribute_accounts(self, count: int) -> List[Account]:
        """توزيع الحسابات للاستخدام المتوازي"""
        available_accounts = self.get_available_accounts()
        
        if not available_accounts:
            return []
        
        if len(available_accounts) <= count:
            return available_accounts
        
        # اختيار عشوائي من أفضل الحسابات
        top_accounts = available_accounts[:min(count * 2, len(available_accounts))]
        return random.sample(top_accounts, min(count, len(top_accounts)))
    
    def rotate_accounts(self) -> List[Account]:
        """دوران الحسابات لتوزيع الحمولة"""
        all_accounts = self.db.query(Account).filter(
            and_(
                Account.is_active == True,
                Account.is_banned == False
            )
        ).all()
        
        # إعادة تعيين العدادات للحسابات التي مر عليها ساعة
        current_time = datetime.utcnow()
        reset_accounts = []
        
        for account in all_accounts:
            if (account.hour_reset_time is None or 
                current_time >= account.hour_reset_time + timedelta(hours=1)):
                
                account.current_hour_requests = 0
                account.hour_reset_time = current_time
                reset_accounts.append(account)
        
        if reset_accounts:
            self.db.commit()
        
        return reset_accounts
    
    def check_account_health(self, account_id: int) -> Dict[str, Any]:
        """فحص صحة حساب محدد"""
        account = self.db.query(Account).filter(Account.id == account_id).first()
        
        if not account:
            return {"error": "Account not found"}
        
        health_status = {
            "account_id": account.id,
            "name": account.name,
            "is_healthy": True,
            "issues": [],
            "recommendations": [],
            "statistics": {
                "total_requests": account.request_count,
                "success_rate": account.success_rate,
                "remaining_requests": account.remaining_requests,
                "last_used": account.last_used.isoformat() if account.last_used else None
            }
        }
        
        # فحص المشاكل المحتملة
        if not account.is_active:
            health_status["is_healthy"] = False
            health_status["issues"].append("Account is inactive")
        
        if account.is_banned:
            health_status["is_healthy"] = False
            health_status["issues"].append(f"Account is banned: {account.ban_reason}")
        
        if account.success_rate < 70:
            health_status["is_healthy"] = False
            health_status["issues"].append(f"Low success rate: {account.success_rate:.1f}%")
            health_status["recommendations"].append("Check account token validity")
        
        if account.remaining_requests == 0:
            health_status["issues"].append("Rate limit reached")
            health_status["recommendations"].append("Wait for rate limit reset or add more accounts")
        
        if account.request_count > 0 and account.success_rate == 0:
            health_status["is_healthy"] = False
            health_status["issues"].append("All requests failed")
            health_status["recommendations"].append("Check account credentials and network connectivity")
        
        return health_status
    
    def auto_ban_problematic_accounts(self) -> List[Dict[str, Any]]:
        """حظر تلقائي للحسابات المشكوك فيها"""
        problematic_accounts = self.db.query(Account).filter(
            and_(
                Account.is_active == True,
                Account.is_banned == False,
                Account.request_count >= 10,  # على الأقل 10 طلبات للتقييم
                Account.successful_requests == 0  # كل الطلبات فاشلة
            )
        ).all()
        
        banned_accounts = []
        
        for account in problematic_accounts:
            # فحص إضافي: إذا كانت آخر 10 طلبات فاشلة
            if account.failed_requests >= 10:
                account.is_banned = True
                account.ban_reason = "تلقائي: معدل فشل عالي (جميع الطلبات فاشلة)"
                
                banned_accounts.append({
                    "account_id": account.id,
                    "name": account.name,
                    "reason": account.ban_reason,
                    "failed_requests": account.failed_requests,
                    "success_rate": account.success_rate
                })
        
        if banned_accounts:
            self.db.commit()
        
        return banned_accounts
    
    def optimize_account_usage(self) -> Dict[str, Any]:
        """تحسين استخدام الحسابات"""
        all_accounts = self.db.query(Account).filter(Account.is_active == True).all()
        
        optimization_report = {
            "total_accounts": len(all_accounts),
            "active_accounts": 0,
            "banned_accounts": 0,
            "available_accounts": 0,
            "optimizations_applied": []
        }
        
        for account in all_accounts:
            if account.is_banned:
                optimization_report["banned_accounts"] += 1
            else:
                optimization_report["active_accounts"] += 1
                
                if account.can_make_request():
                    optimization_report["available_accounts"] += 1
        
        # تطبيق التحسينات
        
        # 1. إعادة تعيين العدادات للحسابات المؤهلة
        reset_accounts = self.rotate_accounts()
        if reset_accounts:
            optimization_report["optimizations_applied"].append(
                f"Reset rate limits for {len(reset_accounts)} accounts"
            )
        
        # 2. حظر الحسابات المشكوك فيها
        banned_accounts = self.auto_ban_problematic_accounts()
        if banned_accounts:
            optimization_report["optimizations_applied"].append(
                f"Auto-banned {len(banned_accounts)} problematic accounts"
            )
            optimization_report["banned_accounts"] += len(banned_accounts)
        
        # 3. تحديث إحصائيات الاستخدام
        self._update_usage_statistics()
        optimization_report["optimizations_applied"].append("Updated usage statistics")
        
        return optimization_report
    
    def _update_usage_statistics(self):
        """تحديث إحصائيات الاستخدام"""
        # يمكن إضافة منطق تحديث الإحصائيات هنا
        # مثل حساب متوسط أوقات الاستجابة، معدلات النجاح، إلخ
        pass
    
    def get_usage_report(self, days: int = 7) -> Dict[str, Any]:
        """تقرير استخدام الحسابات"""
        from datetime import datetime, timedelta
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        accounts = self.db.query(Account).all()
        
        report = {
            "period": f"Last {days} days",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "summary": {
                "total_accounts": len(accounts),
                "active_accounts": len([a for a in accounts if a.is_active]),
                "banned_accounts": len([a for a in accounts if a.is_banned]),
                "total_requests": sum(a.request_count for a in accounts),
                "successful_requests": sum(a.successful_requests for a in accounts),
                "failed_requests": sum(a.failed_requests for a in accounts),
                "overall_success_rate": 0.0
            },
            "account_details": []
        }
        
        # حساب معدل النجاح الإجمالي
        total_requests = report["summary"]["total_requests"]
        if total_requests > 0:
            report["summary"]["overall_success_rate"] = (
                report["summary"]["successful_requests"] / total_requests
            ) * 100
        
        # تفاصيل كل حساب
        for account in accounts:
            account_info = {
                "id": account.id,
                "name": account.name,
                "is_active": account.is_active,
                "is_banned": account.is_banned,
                "total_requests": account.request_count,
                "successful_requests": account.successful_requests,
                "failed_requests": account.failed_requests,
                "success_rate": account.success_rate,
                "last_used": account.last_used.isoformat() if account.last_used else None,
                "remaining_requests": account.remaining_requests
            }
            report["account_details"].append(account_info)
        
        return report