"""
خدمة التعامل مع HelloCallers API
"""
import asyncio
import random
import time
import base64
import hashlib
from typing import Dict, List, Optional, Any
import httpx
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.account import Account
from app.models.proxy import Proxy
from app.models.session import Session as SessionModel


class HelloCallersService:
    def __init__(self, db: Session):
        self.db = db
        self.base_url = settings.HELLOCALLERS_BASE_URL
        
        # Device fingerprints للمحاكاة الواقعية
        self.device_fingerprints = [
            {
                "user_agent": "Dalvik/2.1.0 (Linux; U; Android 11; SM-A505F Build/RP1A.200720.012)",
                "device_model": "SM-A505F",
                "android_version": "11"
            },
            {
                "user_agent": "Dalvik/2.1.0 (Linux; U; Android 12; SM-G991B Build/SP1A.210812.016)",
                "device_model": "SM-G991B", 
                "android_version": "12"
            },
            {
                "user_agent": "Dalvik/2.1.0 (Linux; U; Android 10; Pixel 4 Build/QQ3A.200805.001)",
                "device_model": "Pixel 4",
                "android_version": "10"
            },
            {
                "user_agent": "okhttp/5.0.0-alpha.2",
                "device_model": "Generic",
                "android_version": "11"
            }
        ]
    
    def get_available_account(self) -> Optional[Account]:
        """الحصول على حساب متاح"""
        accounts = self.db.query(Account).filter(
            Account.is_active == True,
            Account.is_banned == False
        ).all()
        
        available_accounts = [acc for acc in accounts if acc.can_make_request()]
        
        if not available_accounts:
            # إذا لم يكن هناك حسابات متاحة، استخدم الأقل استخداماً
            if accounts:
                return min(accounts, key=lambda x: x.current_hour_requests)
            return None
        
        # اختيار عشوائي من الحسابات المتاحة
        return random.choice(available_accounts)
    
    def get_available_proxy(self) -> Optional[Proxy]:
        """الحصول على بروكسي متاح"""
        proxies = self.db.query(Proxy).filter(
            Proxy.is_active == True,
            Proxy.is_working == True
        ).all()
        
        if not proxies:
            return None
        
        # اختيار أفضل بروكسي بناءً على معدل النجاح
        working_proxies = [p for p in proxies if p.can_handle_request()]
        
        if working_proxies:
            # اختيار البروكسي بأفضل معدل نجاح
            return max(working_proxies, key=lambda x: x.success_rate)
        
        return random.choice(proxies)
    
    def generate_realistic_headers(self, account: Account, fingerprint: Dict = None) -> Dict[str, str]:
        """إنشاء headers واقعية"""
        if not fingerprint:
            fingerprint = random.choice(self.device_fingerprints)
        
        return {
            "authorization": f"Bearer {account.token}",
            "api-version": "1",
            "x-request-encrypted": "1",
            "accept": "application/json",
            "device-type": "android",
            "android-app": "main",
            "locale": account.locale or "ar",
            "player-id": account.player_id,
            "device-id": account.device_id,
            "country": account.country or "IQ",
            "content-type": "application/x-www-form-urlencoded",
            "user-agent": fingerprint["user_agent"],
            "accept-encoding": "gzip",
            "connection": "Keep-Alive",
            "host": "hellocallers.com"
        }
    
    def create_encrypted_payload(self, phone_number: str) -> str:
        """إنشاء payload مشفر محاكي"""
        # تحويل رقم الهاتف إلى base64
        phone_base64 = base64.b64encode(phone_number.encode()).decode()
        
        # إنشاء مفتاح عشوائي للتشفير المحاكي
        random_key = hashlib.md5(f"{phone_number}{time.time()}".encode()).hexdigest()[:16]
        encrypted_data = base64.b64encode(random_key.encode()).decode()
        
        return f"{phone_base64}=={encrypted_data}"
    
    async def search_single_phone(
        self, 
        phone_number: str,
        account: Account = None,
        proxy: Proxy = None
    ) -> Dict[str, Any]:
        """البحث عن رقم هاتف واحد"""
        
        # إنشاء جلسة تتبع
        session_id = f"session_{int(time.time())}_{random.randint(1000, 9999)}"
        session = SessionModel(
            session_id=session_id,
            phone_number=phone_number,
            request_type="single",
            status="pending"
        )
        
        try:
            # اختيار حساب إذا لم يتم تحديده
            if not account:
                account = self.get_available_account()
                if not account:
                    raise Exception("No available accounts")
            
            session.account_id = account.id
            
            # اختيار بروكسي إذا لم يتم تحديده
            if not proxy:
                proxy = self.get_available_proxy()
            
            if proxy:
                session.proxy_id = proxy.id
                session.ip_address = proxy.ip_address
            
            # حفظ الجلسة
            self.db.add(session)
            self.db.commit()
            
            # إعداد العميل
            timeout = httpx.Timeout(settings.REQUEST_TIMEOUT)
            proxy_url = proxy.proxy_url if proxy else None
            
            async with httpx.AsyncClient(
                timeout=timeout,
                proxies=proxy_url,
                follow_redirects=True
            ) as client:
                
                # إنشاء headers واقعية
                fingerprint = random.choice(self.device_fingerprints)
                headers = self.generate_realistic_headers(account, fingerprint)
                session.user_agent = fingerprint["user_agent"]
                
                # إنشاء payload مشفر
                encrypted_payload = self.create_encrypted_payload(phone_number)
                
                data = {"payload": encrypted_payload}
                session.request_size = len(str(data))
                
                # تأخير عشوائي لمحاكاة السلوك البشري
                await asyncio.sleep(random.uniform(0.5, 2.0))
                
                # إرسال الطلب
                start_time = time.time()
                response = await client.post(
                    f"{self.base_url}/api/search/contact",
                    headers=headers,
                    data=data
                )
                end_time = time.time()
                
                # تحديث إحصائيات الحساب والبروكسي
                response_time = end_time - start_time
                session.response_size = len(response.content)
                
                if response.status_code == 200:
                    result = response.json()
                    session.response_data = str(result)
                    
                    # تحديث معلومات الجلسة
                    if result.get("status") and result.get("data", {}).get("contacts", {}).get("data"):
                        contact_data = result["data"]["contacts"]["data"][0]
                        
                        session.contact_found = True
                        session.contact_name = contact_data.get("names", [{}])[0].get("name", "غير معروف")
                        session.carrier_name = contact_data.get("carrier_name", "غير معروف")
                        session.country_code = contact_data.get("iso_code", "")
                        session.is_spam = bool(contact_data.get("is_spam", 0))
                        
                        # تحديث إحصائيات
                        account.increment_request_count(True)
                        if proxy:
                            proxy.increment_request_count(True, response_time)
                        
                        session.mark_completed(True)
                        self.db.commit()
                        
                        return {
                            "success": True,
                            "phone_number": phone_number,
                            "session_id": session_id,
                            "data": contact_data,
                            "account_used": account.id,
                            "proxy_used": proxy.id if proxy else None,
                            "response_time": response_time
                        }
                    else:
                        # لا توجد بيانات
                        account.increment_request_count(True)
                        if proxy:
                            proxy.increment_request_count(True, response_time)
                        
                        session.mark_completed(True, "No data found")
                        self.db.commit()
                        
                        return {
                            "success": False,
                            "phone_number": phone_number,
                            "session_id": session_id,
                            "error": "No data found",
                            "account_used": account.id,
                            "proxy_used": proxy.id if proxy else None,
                            "response_time": response_time
                        }
                else:
                    # خطأ HTTP
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    
                    account.increment_request_count(False)
                    if proxy:
                        proxy.increment_request_count(False, response_time)
                    
                    session.mark_completed(False, error_msg)
                    self.db.commit()
                    
                    return {
                        "success": False,
                        "phone_number": phone_number,
                        "session_id": session_id,
                        "error": error_msg,
                        "account_used": account.id,
                        "proxy_used": proxy.id if proxy else None,
                        "response_time": response_time
                    }
                    
        except Exception as e:
            # خطأ عام
            error_msg = str(e)
            
            if account:
                account.increment_request_count(False)
            if proxy:
                proxy.increment_request_count(False, 0)
            
            session.mark_completed(False, error_msg)
            self.db.commit()
            
            return {
                "success": False,
                "phone_number": phone_number,
                "session_id": session_id,
                "error": error_msg,
                "account_used": account.id if account else None,
                "proxy_used": proxy.id if proxy else None,
                "response_time": 0
            }
    
    async def bulk_search_phones(
        self,
        phone_numbers: List[str],
        max_concurrent: int = 5,
        delay_between_requests: float = 1.0
    ) -> Dict[str, Any]:
        """البحث المجمع عن أرقام متعددة"""
        
        if len(phone_numbers) > 100:
            raise ValueError("Maximum 100 phone numbers per bulk request")
        
        results = []
        errors = []
        successful_count = 0
        
        # تحديد حد الطلبات المتزامنة
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def search_with_semaphore(phone_number: str):
            async with semaphore:
                # توزيع الطلبات على حسابات وبروكسيات مختلفة
                account = self.get_available_account()
                proxy = self.get_available_proxy()
                
                result = await self.search_single_phone(phone_number, account, proxy)
                
                # تأخير بين الطلبات
                if delay_between_requests > 0:
                    await asyncio.sleep(delay_between_requests)
                
                return result
        
        # تنفيذ البحث المتوازي
        tasks = [search_with_semaphore(phone) for phone in phone_numbers]
        search_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # معالجة النتائج
        for result in search_results:
            if isinstance(result, Exception):
                errors.append(str(result))
            else:
                results.append(result)
                if result["success"]:
                    successful_count += 1
                else:
                    errors.append(f"{result['phone_number']}: {result['error']}")
        
        return {
            "total_searched": len(phone_numbers),
            "successful_results": successful_count,
            "failed_searches": len(phone_numbers) - successful_count,
            "results": results,
            "errors": errors,
            "timestamp": datetime.utcnow().isoformat()
        }