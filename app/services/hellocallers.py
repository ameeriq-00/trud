"""
خدمة HelloCallers محسنة بناءً على تحليل APK
استبدل app/services/hellocallers.py بهذا الكود
"""
import asyncio
import httpx
import json
import random
import time
import logging
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.utils.helpers import generate_session_id
from app.models.account import Account
from app.models.proxy import Proxy
from app.models.session import Session as SessionModel

# استيراد النظام المتقدم
try:
    from app.utils.advanced_encryption import (
        HelloCallersAdvancedEncryption, 
        create_advanced_hellocallers_request
    )
    ADVANCED_ENCRYPTION_AVAILABLE = True
except ImportError:
    # fallback للنظام القديم
    from app.utils.encryption import HelloCallersEncryption
    ADVANCED_ENCRYPTION_AVAILABLE = False

logger = logging.getLogger(__name__)


class HelloCallersServiceAPK:
    """
    خدمة HelloCallers محسنة بناءً على تحليل APK
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.base_url = "https://hellocallers.com"
        
        # تهيئة نظام التشفير المتقدم
        if ADVANCED_ENCRYPTION_AVAILABLE:
            self.advanced_encryption = HelloCallersAdvancedEncryption()
            self.use_advanced = True
            logger.info("🔐 استخدام نظام التشفير المتقدم")
        else:
            self.encryption = HelloCallersEncryption()
            self.use_advanced = False
            logger.info("⚠️ استخدام نظام التشفير الأساسي")
        
        # Endpoints مُستخرجة من HAR وAPK
        self.endpoints = {
            "histories_all": "/api/user/histories/all",  # الأساسي من HAR
            "user_info": "/api/user/info",
            "search_direct": "/api/search",  # محتمل
            "phone_lookup": "/api/phone/lookup",  # محتمل
        }
        
        # User agents من APK
        self.user_agents = [
            "okhttp/5.0.0-alpha.2",  # من HAR
            "okhttp/4.12.0",
            "Dalvik/2.1.0 (Linux; U; Android 11; SM-A505F Build/RP1A.200720.012)"
        ]
    
    def _get_available_account(self, account_id: Optional[int] = None) -> Optional[Account]:
        """الحصول على حساب متاح"""
        
        query = self.db.query(Account).filter(
            Account.is_active == True,
            Account.is_banned == False
        )
        
        if account_id:
            account = query.filter(Account.id == account_id).first()
            if account and self._can_use_account(account):
                return account
            return None
        
        available_accounts = query.all()
        for account in available_accounts:
            if self._can_use_account(account):
                return account
        
        return None
    
    def _can_use_account(self, account: Account) -> bool:
        """فحص إمكانية استخدام الحساب"""
        current_time = datetime.utcnow()
        
        if account.hour_reset_time and current_time > account.hour_reset_time:
            account.current_hour_requests = 0
            account.hour_reset_time = current_time + timedelta(hours=1)
            self.db.commit()
        
        return account.current_hour_requests < account.rate_limit
    
    def _get_available_proxy(self, proxy_id: Optional[int] = None) -> Optional[Proxy]:
        """الحصول على بروكسي متاح"""
        
        query = self.db.query(Proxy).filter(
            Proxy.is_active == True,
            Proxy.is_working == True
        )
        
        if proxy_id:
            return query.filter(Proxy.id == proxy_id).first()
        
        proxies = query.all()
        return random.choice(proxies) if proxies else None
    
    def _create_advanced_request(self, phone_number: str, account: Account) -> Dict[str, Any]:
        """إنشاء طلب متقدم باستخدام APK analysis"""
        
        if self.use_advanced:
            # استخدام النظام المتقدم
            request_data = create_advanced_hellocallers_request(phone_number, account.token)
            
            # تحديث device info من الحساب
            if account.device_id:
                request_data['device_info']['device_id'] = account.device_id
            if account.player_id:
                request_data['device_info']['player_id'] = account.player_id
            
            return request_data
        else:
            # fallback للنظام القديم
            account_data = {
                "user_id": str(account.id),
                "token": account.token,
                "device_id": account.device_id,
                "player_id": account.player_id,
                "country": account.country,
                "locale": account.locale
            }
            
            headers = self.encryption.get_realistic_headers(account_data, "search")
            payload = self.encryption.encrypt_phone_search(phone_number)
            
            return {
                "url": f"{self.base_url}/api/user/histories/all",
                "method": "POST",
                "headers": headers,
                "data": {"payload": payload},
                "device_info": account_data,
                "payload_analysis": {"advanced": False}
            }
    
    async def search_single_phone(
        self, 
        phone_number: str,
        account_id: Optional[int] = None,
        proxy_id: Optional[int] = None,
        debug_mode: bool = False
    ) -> Dict[str, Any]:
        """
        البحث عن رقم هاتف مع النظام المحسن
        """
        session_id = generate_session_id()
        start_time = time.time()
        
        # إنشاء جلسة
        session = SessionModel(
            session_id=session_id,
            phone_number=phone_number,
            request_type="single",
            status="pending",
            started_at=datetime.utcnow()
        )
        self.db.add(session)
        self.db.commit()
        
        try:
            # اختيار حساب وبروكسي
            account = self._get_available_account(account_id)
            if not account:
                raise Exception("No available accounts")
            
            proxy = self._get_available_proxy(proxy_id)
            
            # تحديث الجلسة
            session.account_id = account.id
            session.proxy_id = proxy.id if proxy else None
            self.db.commit()
            
            # إنشاء الطلب المتقدم
            request_data = self._create_advanced_request(phone_number, account)
            
            # حفظ payload للتصحيح
            session.payload_used = request_data['data']['payload']
            self.db.commit()
            
            if debug_mode:
                print("🔐 Advanced Request Generated:")
                print(f"📱 Device Info: {request_data['device_info']}")
                print(f"🔑 Payload: {request_data['data']['payload']}")
                print(f"📊 Analysis: {request_data.get('payload_analysis', {})}")
                print(f"🌐 URL: {request_data['url']}")
            
            # إعداد HTTP client
            timeout = httpx.Timeout(30.0)
            proxy_url = None
            
            if proxy:
                if proxy.username and proxy.password:
                    proxy_url = f"http://{proxy.username}:{proxy.password}@{proxy.host}:{proxy.port}"
                else:
                    proxy_url = f"http://{proxy.host}:{proxy.port}"
            
            # تجريب endpoints مختلفة
            endpoints_to_try = [
                request_data['url'],  # الـ URL المُولد
                f"{self.base_url}/api/user/histories/all",  # من HAR
                f"{self.base_url}/api/search",  # محتمل
                f"{self.base_url}/api/phone/lookup",  # محتمل
            ]
            
            last_error = None
            
            for endpoint_url in endpoints_to_try:
                try:
                    if debug_mode:
                        print(f"🌐 جاري المحاولة: {endpoint_url}")
                    
                    async with httpx.AsyncClient(
                        timeout=timeout,
                        proxies=proxy_url,
                        verify=False
                    ) as client:
                        
                        # تحديث URL في request data
                        current_request = request_data.copy()
                        current_request['url'] = endpoint_url
                        
                        response = await client.request(
                            method=current_request['method'],
                            url=endpoint_url,
                            headers=current_request['headers'],
                            data=current_request['data']
                        )
                        
                        response_time = time.time() - start_time
                        
                        if debug_mode:
                            print(f"📡 Response status: {response.status_code}")
                            print(f"📄 Response headers: {dict(response.headers)}")
                            print(f"📝 Response text (first 500 chars): {response.text[:500]}")
                        
                        # تحليل الاستجابة
                        result = await self._parse_response(
                            response, 
                            session, 
                            account, 
                            response_time,
                            endpoint_url,
                            debug_mode
                        )
                        
                        # تحديث إحصائيات
                        self._update_account_stats(account, result["success"])
                        if proxy:
                            self._update_proxy_stats(proxy, result["success"], response_time)
                        
                        # إضافة معلومات إضافية للنتيجة
                        result.update({
                            "encryption_method": "Advanced APK-based" if self.use_advanced else "Basic",
                            "endpoint_used": endpoint_url,
                            "payload_analysis": request_data.get('payload_analysis', {}),
                            "device_info": request_data['device_info']
                        })
                        
                        return result
                        
                except Exception as e:
                    last_error = str(e)
                    if debug_mode:
                        print(f"❌ خطأ مع {endpoint_url}: {str(e)}")
                    continue
            
            # إذا فشلت جميع المحاولات
            raise Exception(f"جميع endpoints فشلت. آخر خطأ: {last_error}")
                
        except Exception as e:
            # تسجيل الخطأ
            session.status = "failed"
            session.error_message = str(e)
            session.completed_at = datetime.utcnow()
            self.db.commit()
            
            logger.error(f"Error in search_single_phone: {str(e)}")
            
            return {
                "success": False,
                "phone_number": phone_number,
                "session_id": session_id,
                "error": str(e),
                "response_time": time.time() - start_time,
                "encryption_method": "Advanced APK-based" if self.use_advanced else "Basic"
            }
    
    async def _parse_response(
        self, 
        response: httpx.Response, 
        session: SessionModel, 
        account: Account, 
        response_time: float,
        url: str,
        debug_mode: bool = False
    ) -> Dict[str, Any]:
        """تحليل استجابة API محسن"""
        
        try:
            # محاولة تحليل JSON
            try:
                response_data = response.json()
            except:
                # إذا لم يكن JSON صحيح
                response_data = {
                    "status": response.status_code == 200,
                    "code": response.status_code,
                    "msg": response.text[:200] if response.text else "Empty response",
                    "data": None
                }
            
            if debug_mode:
                print(f"📋 Parsed response data: {response_data}")
            
            # تحليل مُفصل للاستجابة
            is_success = self._determine_success(response, response_data)
            
            # استخراج البيانات
            data = response_data.get("data")
            contact_info = self._extract_contact_info(data) if data else None
            
            # تحديث الجلسة
            session.status = "completed" if is_success else "failed"
            session.response_time = response_time
            session.completed_at = datetime.utcnow()
            
            if contact_info:
                session.contact_found = True
                session.contact_name = contact_info.get("name")
                session.carrier_name = contact_info.get("carrier")
                session.country_code = contact_info.get("country_code")
                session.is_spam = contact_info.get("is_spam", False)
            else:
                session.contact_found = False
            
            if not is_success:
                error_msg = self._extract_error_message(response_data, response.status_code)
                session.error_message = error_msg
            
            self.db.commit()
            
            return {
                "success": is_success,
                "phone_number": session.phone_number,
                "session_id": session.session_id,
                "data": contact_info,
                "error": session.error_message if not is_success else None,
                "account_used": account.id,
                "response_time": response_time,
                "url_used": url,
                "status_code": response.status_code,
                "raw_response": response_data,
                "response_analysis": self._analyze_response_patterns(response_data)
            }
            
        except Exception as e:
            session.status = "failed"
            session.error_message = f"Parse error: {str(e)}"
            session.completed_at = datetime.utcnow()
            self.db.commit()
            
            return {
                "success": False,
                "phone_number": session.phone_number,
                "session_id": session.session_id,
                "error": f"Failed to parse response: {str(e)}",
                "response_time": response_time,
                "raw_response": response.text[:500] if hasattr(response, 'text') else str(response)
            }
    
    def _determine_success(self, response: httpx.Response, response_data: Dict[str, Any]) -> bool:
        """تحديد نجاح الطلب بطريقة ذكية"""
        
        # فحص HTTP status code
        if response.status_code != 200:
            return False
        
        # فحص بنية الاستجابة
        status = response_data.get("status", False)
        code = response_data.get("code", 0)
        
        # أنماط النجاح المختلفة
        success_patterns = [
            status == True and code == 200,
            status == "success",
            code == 200 and "data" in response_data,
            "success" in response_data.get("msg", "").lower(),
        ]
        
        return any(success_patterns)
    
    def _extract_error_message(self, response_data: Dict[str, Any], status_code: int) -> str:
        """استخراج رسالة الخطأ"""
        
        # أنماط رسائل الخطأ المختلفة
        error_fields = ["msg", "message", "error", "error_message", "detail"]
        
        for field in error_fields:
            if field in response_data and response_data[field]:
                return str(response_data[field])
        
        # رسائل خطأ حسب HTTP status
        status_messages = {
            400: "Bad Request - طلب غير صحيح",
            401: "Unauthorized - غير مخول",
            403: "Forbidden - محظور",
            404: "Not Found - غير موجود",
            429: "Rate Limited - تم تجاوز الحد المسموح",
            500: "Server Error - خطأ في الخادم",
            502: "Bad Gateway - خطأ في البوابة",
            503: "Service Unavailable - الخدمة غير متاحة"
        }
        
        return status_messages.get(status_code, f"HTTP {status_code}")
    
    def _analyze_response_patterns(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """تحليل أنماط الاستجابة"""
        
        analysis = {
            "has_data": "data" in response_data,
            "has_status": "status" in response_data,
            "has_code": "code" in response_data,
            "has_msg": "msg" in response_data,
            "data_type": type(response_data.get("data")).__name__ if "data" in response_data else None,
            "total_fields": len(response_data) if isinstance(response_data, dict) else 0
        }
        
        # فحص أنماط البيانات الخاصة بـ HelloCallers
        if analysis["has_data"] and response_data["data"]:
            data = response_data["data"]
            if isinstance(data, dict):
                analysis["contact_fields"] = list(data.keys())
            elif isinstance(data, list) and data:
                analysis["is_list"] = True
                analysis["list_length"] = len(data)
                if isinstance(data[0], dict):
                    analysis["item_fields"] = list(data[0].keys())
        
        return analysis
    
    def _extract_contact_info(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """استخراج معلومات جهة الاتصال محسن"""
        
        if not data:
            return None
        
        contact_info = {}
        
        # أنماط أسماء الحقول المختلفة
        field_mappings = {
            "name": ["name", "contact_name", "caller_name", "display_name", "full_name"],
            "carrier": ["carrier", "operator", "network", "provider", "carrier_name"],
            "location": ["country", "region", "city", "location", "address"],
            "phone_type": ["type", "phone_type", "number_type", "category"],
            "is_spam": ["spam", "is_spam", "spam_score", "reported_as_spam"],
            "country_code": ["country_code", "country_id", "cc"]
        }
        
        # استخراج المعلومات باستخدام الأنماط
        for info_key, possible_fields in field_mappings.items():
            for field in possible_fields:
                if field in data and data[field]:
                    contact_info[info_key] = data[field]
                    break
        
        # معالجة خاصة للبيانات المعقدة
        if isinstance(data, list) and data:
            # إذا كانت البيانات عبارة عن قائمة، خذ أول عنصر
            return self._extract_contact_info(data[0])
        
        # فحص البيانات المتداخلة
        nested_fields = ["contact", "caller", "number_info", "phone_data"]
        for nested_field in nested_fields:
            if nested_field in data and isinstance(data[nested_field], dict):
                nested_info = self._extract_contact_info(data[nested_field])
                if nested_info:
                    contact_info.update(nested_info)
        
        return contact_info if contact_info else None
    
    def _update_account_stats(self, account: Account, success: bool):
        """تحديث إحصائيات الحساب"""
        account.request_count += 1
        account.current_hour_requests += 1
        account.last_used = datetime.utcnow()
        
        if success:
            account.successful_requests += 1
        else:
            account.failed_requests += 1
        
        self.db.commit()
    
    def _update_proxy_stats(self, proxy: Proxy, success: bool, response_time: float):
        """تحديث إحصائيات البروكسي"""
        proxy.total_requests += 1
        
        if success:
            proxy.successful_requests += 1
        else:
            proxy.failed_requests += 1
        
        # تحديث متوسط وقت الاستجابة
        if proxy.total_requests == 1:
            proxy.average_response_time = response_time
        else:
            proxy.average_response_time = (
                (proxy.average_response_time * (proxy.total_requests - 1) + response_time) 
                / proxy.total_requests
            )
        
        self.db.commit()
    
    async def test_advanced_encryption(self, phone_number: str) -> Dict[str, Any]:
        """اختبار نظام التشفير المتقدم"""
        
        if not self.use_advanced:
            return {"error": "Advanced encryption not available"}
        
        try:
            # إنشاء device info تجريبي
            device_info = self.advanced_encryption.generate_realistic_device_fingerprint()
            
            # إنشاء payload متقدم
            payload = self.advanced_encryption.create_advanced_payload(phone_number, device_info)
            
            # تحليل الـ payload
            analysis = self.advanced_encryption.analyze_and_compare_with_har(payload)
            
            return {
                "success": True,
                "phone_number": phone_number,
                "device_info": device_info,
                "payload": payload,
                "analysis": analysis,
                "encryption_method": "Advanced AES/CBC/PKCS7"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "encryption_method": "Advanced (failed)"
            }
    
    def get_service_info(self) -> Dict[str, Any]:
        """معلومات الخدمة"""
        
        return {
            "service_name": "HelloCallers Service APK Enhanced",
            "encryption_type": "Advanced APK-based" if self.use_advanced else "Basic",
            "supported_endpoints": list(self.endpoints.keys()),
            "user_agents": self.user_agents,
            "package_info": {
                "package": "com.callerid.wie",
                "version": "1.6.6",
                "version_code": "120"
            } if self.use_advanced else None
        }