# app/services/hellocallers.py - إصدار محسن بناءً على تحليل HAR

"""
خدمة HelloCallers محسنة بناءً على تحليل ملف HAR
"""
import asyncio
import httpx
import json
import random
import time
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from datetime import datetime

from app.utils.helpers import (
    generate_session_id, 
    normalize_phone_number,
    generate_android_fingerprint,
    get_random_delay
)
from app.utils.encryption import EnhancedEncryption
from app.models.account import Account
from app.models.proxy import Proxy
from app.models.session import Session as SessionModel


class HelloCallersService:
    """
    خدمة HelloCallers محسنة مع محاكاة كاملة للـ API الحقيقي
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.base_url = "https://hellocallers.com"
        self.encryption = EnhancedEncryption()
        
        # User agents واقعية من تحليل HAR
        self.user_agents = [
            "okhttp/5.0.0-alpha.2",
            "okhttp/4.12.0", 
            "okhttp/5.0.0",
            "Dalvik/2.1.0 (Linux; U; Android 11; SM-A505F Build/RP1A.200720.012)",
            "Dalvik/2.1.0 (Linux; U; Android 12; SM-G973F Build/SP1A.210812.016)",
            "Dalvik/2.1.0 (Linux; U; Android 13; Pixel 6 Build/TQ3A.230901.001)"
        ]
        
        # Device fingerprints مستخرجة من HAR
        self.device_templates = [
            {
                "device_id": "e89fdbf136ae2460",
                "player_id": "df33b4ce-9b1e-49ed-8ce0-44f1dbc89988",
                "android_version": "11",
                "device_model": "SM-A505F"
            },
            # يمكن إضافة المزيد من القوالب
        ]
    
    def get_realistic_headers(self, account: Account, endpoint: str = "search") -> Dict[str, str]:
        """
        إنشاء headers واقعية بناءً على تحليل HAR
        """
        device_info = random.choice(self.device_templates).copy()
        
        # تخصيص معلومات الجهاز للحساب
        if account.device_id:
            device_info["device_id"] = account.device_id
        if account.player_id:
            device_info["player_id"] = account.player_id
        
        headers = {
            "authorization": f"Bearer {account.token}",
            "api-version": "1",
            "x-request-encrypted": "1",
            "accept": "application/json",
            "device-type": "android",
            "android-app": "main",
            "locale": account.locale or "ar",
            "player-id": device_info["player_id"],
            "device-id": device_info["device_id"],
            "country": account.country or "IQ",
            "host": "hellocallers.com",
            "connection": "Keep-Alive",
            "accept-encoding": "gzip",
            "user-agent": random.choice(self.user_agents)
        }
        
        # إضافة headers خاصة حسب نوع الطلب
        if endpoint in ["search", "histories"]:
            headers["content-type"] = "application/x-www-form-urlencoded"
        elif endpoint == "user_info":
            headers["content-type"] = "application/json"
        
        return headers
    
    def create_realistic_payload(self, phone_number: str, request_type: str = "search") -> str:
        """
        إنشاء payload مشفر محاكي للأنماط المكتشفة في HAR
        """
        if request_type == "search":
            # للبحث عن رقم
            clean_phone = phone_number.replace('+', '').replace(' ', '').replace('-', '')
            return self.encryption.encrypt_phone_search(clean_phone)
        
        elif request_type == "history_all":
            # لجلب تاريخ البحث
            return self.encryption.encrypt_history_request()
        
        elif request_type == "add_history":
            # لإضافة البحث للتاريخ
            return self.encryption.encrypt_with_session(phone_number)
        
        else:
            return self.encryption.generate_realistic_payload(phone_number)
    
    async def search_single_phone(
        self, 
        phone_number: str,
        account: Account = None,
        proxy: Proxy = None
    ) -> Dict[str, Any]:
        """
        البحث عن رقم هاتف واحد مع محاكاة كاملة لسلوك HelloCallers
        """
        session_id = generate_session_id()
        start_time = time.time()
        
        # إنشاء جلسة جديدة
        session = SessionModel(
            session_id=session_id,
            phone_number=phone_number,
            request_type="single",
            status="pending",
            started_at=datetime.utcnow()
        )
        
        try:
            # اختيار حساب وبروكسي إذا لم يتم تحديدهما
            if not account:
                account = self._get_available_account()
            if not proxy:
                proxy = self._get_available_proxy()
            
            if account:
                session.account_id = account.id
            if proxy:
                session.proxy_id = proxy.id
            
            # تطبيع رقم الهاتف
            normalized = normalize_phone_number(phone_number)
            search_phone = normalized["e164"]
            
            # إعداد الطلب
            headers = self.get_realistic_headers(account, "search")
            payload = self.create_realistic_payload(search_phone, "search")
            
            # إعداد البروكسي
            proxy_config = None
            if proxy:
                proxy_config = {
                    "http://": f"http://{proxy.username}:{proxy.password}@{proxy.host}:{proxy.port}",
                    "https://": f"http://{proxy.username}:{proxy.password}@{proxy.host}:{proxy.port}"
                } if proxy.username else f"http://{proxy.host}:{proxy.port}"
            
            # تأخير عشوائي لتجنب الكشف
            await asyncio.sleep(get_random_delay(0.5, 2.0))
            
            # إجراء الطلب
            async with httpx.AsyncClient(
                timeout=30.0,
                proxies=proxy_config,
                follow_redirects=True
            ) as client:
                
                # الطلب الأول: البحث عن الرقم
                search_response = await client.post(
                    f"{self.base_url}/api/search/contact",
                    headers=headers,
                    data={"payload": payload}
                )
                
                response_time = time.time() - start_time
                session.response_time = response_time
                
                if search_response.status_code == 200:
                    result_data = search_response.json()
                    
                    if result_data.get("status") and result_data.get("data"):
                        # استخراج معلومات الرقم
                        contacts = result_data["data"].get("data", [])
                        
                        if contacts:
                            contact = contacts[0]
                            contact_info = {
                                "phone_number": normalized["international"],
                                "national": contact.get("national", ""),
                                "international": contact.get("international", ""),
                                "e164": contact.get("e164", ""),
                                "country": contact.get("country_name", ""),
                                "carrier": contact.get("carrier_name", ""),
                                "carrier_type": contact.get("carrier_type_text", ""),
                                "is_spam": bool(contact.get("is_spam", 0)),
                                "names": [name.get("name", "") for name in contact.get("names", [])],
                                "uuid": contact.get("uuid", "")
                            }
                            
                            # تحديث الجلسة
                            session.status = "success"
                            session.contact_found = True
                            session.contact_name = contact_info["names"][0] if contact_info["names"] else None
                            session.carrier_name = contact_info["carrier"]
                            session.country_code = normalized["country_code"]
                            session.is_spam = contact_info["is_spam"]
                            session.response_data = json.dumps(contact_info, ensure_ascii=False)
                            
                            # محاولة إضافة للتاريخ (محاكياً لسلوك التطبيق)
                            await self._add_to_history(client, headers, search_phone, account)
                            
                            return {
                                "success": True,
                                "phone_number": search_phone,
                                "session_id": session_id,
                                "data": contact_info,
                                "account_used": account.id if account else None,
                                "proxy_used": proxy.id if proxy else None,
                                "response_time": response_time
                            }
                        else:
                            # لم يتم العثور على الرقم
                            session.status = "success"
                            session.contact_found = False
                            
                            return {
                                "success": False,
                                "phone_number": search_phone,
                                "session_id": session_id,
                                "error": "لم يتم العثور على معلومات لهذا الرقم",
                                "account_used": account.id if account else None,
                                "proxy_used": proxy.id if proxy else None,
                                "response_time": response_time
                            }
                    else:
                        # خطأ في الاستجابة
                        error_msg = result_data.get("msg", "خطأ غير معروف")
                        session.status = "failed"
                        session.error_message = error_msg
                        
                        return {
                            "success": False,
                            "phone_number": search_phone,
                            "session_id": session_id,
                            "error": error_msg,
                            "account_used": account.id if account else None,
                            "proxy_used": proxy.id if proxy else None,
                            "response_time": response_time
                        }
                else:
                    # خطأ HTTP
                    error_msg = f"HTTP {search_response.status_code}: {search_response.reason_phrase}"
                    session.status = "failed"
                    session.error_message = error_msg
                    
                    return {
                        "success": False,
                        "phone_number": search_phone,
                        "session_id": session_id,
                        "error": error_msg,
                        "account_used": account.id if account else None,
                        "proxy_used": proxy.id if proxy else None,
                        "response_time": response_time
                    }
        
        except asyncio.TimeoutError:
            session.status = "timeout"
            session.error_message = "انتهت مهلة الاتصال"
            return {
                "success": False,
                "phone_number": phone_number,
                "session_id": session_id,
                "error": "انتهت مهلة الاتصال",
                "response_time": time.time() - start_time
            }
        
        except Exception as e:
            session.status = "failed"
            session.error_message = str(e)
            return {
                "success": False,
                "phone_number": phone_number,
                "session_id": session_id,
                "error": f"خطأ في الطلب: {str(e)}",
                "response_time": time.time() - start_time
            }
        
        finally:
            # حفظ الجلسة
            session.completed_at = datetime.utcnow()
            session.response_time = time.time() - start_time
            self.db.add(session)
            self.db.commit()
    
    async def _add_to_history(self, client: httpx.AsyncClient, headers: Dict[str, str], phone: str, account: Account):
        """
        إضافة البحث لتاريخ المستخدم (محاكاة سلوك التطبيق)
        """
        try:
            # تأخير صغير
            await asyncio.sleep(get_random_delay(0.1, 0.5))
            
            # تحديث headers للتاريخ
            history_headers = headers.copy()
            history_payload = self.create_realistic_payload(phone, "add_history")
            
            await client.post(
                f"{self.base_url}/api/user/histories",
                headers=history_headers,
                data={"payload": history_payload}
            )
        except:
            # تجاهل أخطاء إضافة التاريخ
            pass
    
    async def bulk_search_phones(
        self,
        phone_numbers: List[str],
        max_concurrent: int = 5,
        delay_between_requests: float = 1.0
    ) -> Dict[str, Any]:
        """
        البحث المجمع عن عدة أرقام مع تحكم في السرعة والتزامن
        """
        results = []
        errors = []
        successful_count = 0
        failed_count = 0
        
        # تنظيف وتطبيع الأرقام
        clean_numbers = []
        for phone in phone_numbers:
            try:
                normalized = normalize_phone_number(phone)
                clean_numbers.append(normalized["e164"])
            except:
                errors.append(f"رقم غير صالح: {phone}")
        
        # تقسيم الأرقام إلى مجموعات
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def search_with_semaphore(phone: str):
            async with semaphore:
                try:
                    result = await self.search_single_phone(phone)
                    if result["success"]:
                        nonlocal successful_count
                        successful_count += 1
                    else:
                        nonlocal failed_count
                        failed_count += 1
                    
                    results.append(result)
                    
                    # تأخير بين الطلبات
                    if delay_between_requests > 0:
                        await asyncio.sleep(get_random_delay(
                            delay_between_requests * 0.7, 
                            delay_between_requests * 1.3
                        ))
                    
                except Exception as e:
                    failed_count += 1
                    results.append({
                        "success": False,
                        "phone_number": phone,
                        "error": str(e),
                        "response_time": 0
                    })
        
        # تشغيل البحث المتوازي
        start_time = time.time()
        tasks = [search_with_semaphore(phone) for phone in clean_numbers]
        await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        return {
            "total_searched": len(clean_numbers),
            "successful_results": successful_count,
            "failed_searches": failed_count,
            "results": results,
            "errors": errors,
            "total_time": total_time,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _get_available_account(self) -> Optional[Account]:
        """الحصول على حساب متاح"""
        accounts = self.db.query(Account).filter(
            Account.is_active == True,
            Account.is_banned == False
        ).all()
        
        if not accounts:
            return None
        
        # اختيار الحساب بأقل استخدام
        available_accounts = [acc for acc in accounts if acc.can_handle_request()]
        
        if available_accounts:
            return min(available_accounts, key=lambda x: x.requests_today)
        
        return random.choice(accounts)
    
    def _get_available_proxy(self) -> Optional[Proxy]:
        """الحصول على بروكسي متاح"""
        proxies = self.db.query(Proxy).filter(
            Proxy.is_active == True,
            Proxy.is_working == True
        ).all()
        
        if not proxies:
            return None
        
        # اختيار البروكسي بأفضل معدل نجاح
        working_proxies = [p for p in proxies if p.can_handle_request()]
        
        if working_proxies:
            return max(working_proxies, key=lambda x: x.success_rate)
        
        return random.choice(proxies)
    
    async def validate_account(self, account: Account) -> Dict[str, Any]:
        """
        التحقق من صحة الحساب
        """
        try:
            headers = self.get_realistic_headers(account, "user_info")
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/user/info",
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status"):
                        user_info = data.get("data", {}).get("user", {})
                        return {
                            "valid": True,
                            "user_info": user_info,
                            "rate_limit": {
                                "limit": response.headers.get("x-ratelimit-limit"),
                                "remaining": response.headers.get("x-ratelimit-remaining")
                            }
                        }
                
                return {
                    "valid": False,
                    "error": f"HTTP {response.status_code}",
                    "details": response.text[:200]
                }
        
        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            }
    
    async def test_proxy(self, proxy: Proxy) -> Dict[str, Any]:
        """
        اختبار البروكسي
        """
        try:
            proxy_config = {
                "http://": f"http://{proxy.username}:{proxy.password}@{proxy.host}:{proxy.port}",
                "https://": f"http://{proxy.username}:{proxy.password}@{proxy.host}:{proxy.port}"
            } if proxy.username else f"http://{proxy.host}:{proxy.port}"
            
            start_time = time.time()
            
            async with httpx.AsyncClient(
                timeout=10.0,
                proxies=proxy_config
            ) as client:
                # اختبار الاتصال بـ HelloCallers
                response = await client.get(f"{self.base_url}/")
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    return {
                        "working": True,
                        "response_time": response_time,
                        "status_code": response.status_code
                    }
                else:
                    return {
                        "working": False,
                        "error": f"HTTP {response.status_code}",
                        "response_time": response_time
                    }
        
        except Exception as e:
            return {
                "working": False,
                "error": str(e),
                "response_time": time.time() - start_time if 'start_time' in locals() else 0
            }
    
    async def get_user_search_history(self, account: Account, limit: int = 50) -> Dict[str, Any]:
        """
        جلب تاريخ البحث للمستخدم
        """
        try:
            headers = self.get_realistic_headers(account, "history")
            payload = self.create_realistic_payload("", "history_all")
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/user/histories/all",
                    headers=headers,
                    data={"payload": payload}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status"):
                        contacts = data.get("data", {}).get("contacts", [])
                        return {
                            "success": True,
                            "history": contacts[:limit],
                            "total_count": len(contacts)
                        }
                
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "details": response.text[:200]
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }