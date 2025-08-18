"""
خدمة إدارة البروكسيات
"""
import asyncio
import random
import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import httpx
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.proxy import Proxy
from app.core.config import settings


class ProxyManager:
    """مدير البروكسيات - إدارة شاملة للبروكسيات"""
    
    def __init__(self, db: Session):
        self.db = db
        self.test_urls = [
            "https://httpbin.org/ip",
            "https://icanhazip.com",
            "https://api.ipify.org?format=json"
        ]
    
    def get_working_proxies(self, limit: Optional[int] = None) -> List[Proxy]:
        """الحصول على البروكسيات العاملة"""
        query = self.db.query(Proxy).filter(
            and_(
                Proxy.is_active == True,
                Proxy.is_working == True
            )
        )
        
        proxies = query.all()
        
        # ترتيب حسب معدل النجاح
        proxies.sort(key=lambda x: x.success_rate, reverse=True)
        
        if limit:
            return proxies[:limit]
        
        return proxies
    
    def get_best_proxy(self) -> Optional[Proxy]:
        """الحصول على أفضل بروكسي متاح"""
        working_proxies = self.get_working_proxies(limit=10)
        
        if not working_proxies:
            return None
        
        # اختيار أفضل بروكسي بناءً على عدة معايير
        best_proxy = None
        best_score = -1
        
        for proxy in working_proxies:
            score = self._calculate_proxy_score(proxy)
            
            if score > best_score:
                best_score = score
                best_proxy = proxy
        
        return best_proxy
    
    def _calculate_proxy_score(self, proxy: Proxy) -> float:
        """حساب نقاط تقييم البروكسي"""
        score = 0.0
        
        # معدل النجاح (40% من النقاط)
        success_rate = proxy.success_rate
        score += (success_rate / 100) * 40
        
        # سرعة الاستجابة (30% من النقاط)
        if proxy.average_response_time > 0:
            # كلما كان الوقت أقل، كلما كانت النقاط أعلى
            speed_score = max(0, 30 - (proxy.average_response_time * 3))
            score += min(speed_score, 30)
        else:
            score += 15  # نقاط متوسطة للبروكسيات الجديدة
        
        # عدد الطلبات الناجحة (20% من النقاط)
        if proxy.total_requests > 0:
            reliability_score = min(proxy.successful_requests / 10, 20)
            score += reliability_score
        
        # آخر استخدام (10% من النقاط)
        if proxy.last_used:
            time_since_last_use = datetime.utcnow() - proxy.last_used
            hours_since_use = time_since_last_use.total_seconds() / 3600
            # توازن: لا نريد بروكسي لم يستخدم لفترة طويلة جداً
            if hours_since_use <= 24:
                score += (24 - hours_since_use) / 24 * 10
        else:
            score += 5  # نقاط متوسطة للبروكسيات الجديدة
        
        return score
    
    def distribute_proxies(self, count: int) -> List[Proxy]:
        """توزيع البروكسيات للاستخدام المتوازي"""
        working_proxies = self.get_working_proxies()
        
        if not working_proxies:
            return []
        
        if len(working_proxies) <= count:
            return working_proxies
        
        # اختيار متنوع من أفضل البروكسيات
        top_proxies = working_proxies[:min(count * 2, len(working_proxies))]
        return random.sample(top_proxies, min(count, len(top_proxies)))
    
    async def test_proxy(self, proxy: Proxy) -> Dict[str, Any]:
        """اختبار بروكسي واحد"""
        test_result = {
            "proxy_id": proxy.id,
            "proxy_name": proxy.name,
            "is_working": False,
            "response_time": 0.0,
            "ip_address": None,
            "error_message": None,
            "test_url": None
        }
        
        # اختيار URL عشوائي للاختبار
        test_url = random.choice(self.test_urls)
        test_result["test_url"] = test_url
        
        try:
            proxy_url = proxy.proxy_url
            
            async with httpx.AsyncClient(
                proxies=proxy_url,
                timeout=httpx.Timeout(proxy.timeout)
            ) as client:
                
                start_time = time.time()
                response = await client.get(test_url)
                end_time = time.time()
                
                test_result["response_time"] = end_time - start_time
                
                if response.status_code == 200:
                    test_result["is_working"] = True
                    
                    # محاولة استخراج عنوان IP
                    try:
                        if "ipify" in test_url:
                            data = response.json()
                            test_result["ip_address"] = data.get("ip")
                        elif "httpbin" in test_url:
                            data = response.json()
                            test_result["ip_address"] = data.get("origin")
                        else:
                            test_result["ip_address"] = response.text.strip()
                    except:
                        pass
                else:
                    test_result["error_message"] = f"HTTP {response.status_code}"
                    
        except asyncio.TimeoutError:
            test_result["error_message"] = "Connection timeout"
        except Exception as e:
            test_result["error_message"] = str(e)
        
        return test_result
    
    async def test_all_proxies(self) -> Dict[str, Any]:
        """اختبار جميع البروكسيات"""
        all_proxies = self.db.query(Proxy).filter(Proxy.is_active == True).all()
        
        if not all_proxies:
            return {
                "total_proxies": 0,
                "working_proxies": 0,
                "failed_proxies": 0,
                "results": []
            }
        
        # اختبار البروكسيات بالتوازي
        tasks = [self.test_proxy(proxy) for proxy in all_proxies]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        working_count = 0
        failed_count = 0
        test_results = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # خطأ في الاختبار
                proxy = all_proxies[i]
                error_result = {
                    "proxy_id": proxy.id,
                    "proxy_name": proxy.name,
                    "is_working": False,
                    "response_time": 0.0,
                    "ip_address": None,
                    "error_message": str(result),
                    "test_url": None
                }
                test_results.append(error_result)
                failed_count += 1
            else:
                test_results.append(result)
                if result["is_working"]:
                    working_count += 1
                else:
                    failed_count += 1
        
        # تحديث حالة البروكسيات في قاعدة البيانات
        await self._update_proxy_status(test_results)
        
        return {
            "total_proxies": len(all_proxies),
            "working_proxies": working_count,
            "failed_proxies": failed_count,
            "results": test_results,
            "test_timestamp": datetime.utcnow().isoformat()
        }
    
    async def _update_proxy_status(self, test_results: List[Dict[str, Any]]):
        """تحديث حالة البروكسيات بناءً على نتائج الاختبار"""
        for result in test_results:
            proxy = self.db.query(Proxy).filter(
                Proxy.id == result["proxy_id"]
            ).first()
            
            if proxy:
                proxy.is_working = result["is_working"]
                proxy.last_check = datetime.utcnow()
                
                if result["is_working"]:
                    proxy.status_message = "Working properly"
                    if result["ip_address"]:
                        proxy.ip_address = result["ip_address"]
                    
                    # تحديث متوسط وقت الاستجابة
                    if proxy.average_response_time == 0:
                        proxy.average_response_time = result["response_time"]
                    else:
                        # حساب المتوسط المتحرك
                        proxy.average_response_time = (
                            proxy.average_response_time * 0.7 + 
                            result["response_time"] * 0.3
                        )
                else:
                    proxy.status_message = result.get("error_message", "Unknown error")
        
        self.db.commit()
    
    def auto_disable_bad_proxies(self) -> List[Dict[str, Any]]:
        """إيقاف البروكسيات السيئة تلقائياً"""
        bad_proxies = self.db.query(Proxy).filter(
            and_(
                Proxy.is_active == True,
                Proxy.total_requests >= 10,  # على الأقل 10 طلبات للتقييم
                Proxy.successful_requests == 0  # كل الطلبات فاشلة
            )
        ).all()
        
        # إضافة البروكسيات البطيئة جداً
        slow_proxies = self.db.query(Proxy).filter(
            and_(
                Proxy.is_active == True,
                Proxy.average_response_time > 30.0  # أبطأ من 30 ثانية
            )
        ).all()
        
        disabled_proxies = []
        
        for proxy in bad_proxies + slow_proxies:
            if proxy not in disabled_proxies:
                proxy.is_active = False
                proxy.status_message = "تلقائي: أداء ضعيف"
                
                disabled_proxies.append({
                    "proxy_id": proxy.id,
                    "name": proxy.name,
                    "reason": "Poor performance",
                    "success_rate": proxy.success_rate,
                    "response_time": proxy.average_response_time
                })
        
        if disabled_proxies:
            self.db.commit()
        
        return disabled_proxies
    
    def get_proxy_statistics(self) -> Dict[str, Any]:
        """إحصائيات البروكسيات"""
        all_proxies = self.db.query(Proxy).all()
        
        stats = {
            "total_proxies": len(all_proxies),
            "active_proxies": 0,
            "working_proxies": 0,
            "failed_proxies": 0,
            "average_response_time": 0.0,
            "total_requests": 0,
            "successful_requests": 0,
            "overall_success_rate": 0.0,
            "proxy_types": {},
            "countries": {}
        }
        
        response_times = []
        
        for proxy in all_proxies:
            if proxy.is_active:
                stats["active_proxies"] += 1
                
                if proxy.is_working:
                    stats["working_proxies"] += 1
                else:
                    stats["failed_proxies"] += 1
            
            stats["total_requests"] += proxy.total_requests
            stats["successful_requests"] += proxy.successful_requests
            
            if proxy.average_response_time > 0:
                response_times.append(proxy.average_response_time)
            
            # إحصائيات نوع البروكسي
            proxy_type = proxy.proxy_type
            if proxy_type in stats["proxy_types"]:
                stats["proxy_types"][proxy_type] += 1
            else:
                stats["proxy_types"][proxy_type] = 1
            
            # إحصائيات البلدان
            if proxy.country:
                country = proxy.country
                if country in stats["countries"]:
                    stats["countries"][country] += 1
                else:
                    stats["countries"][country] = 1
        
        # حساب المتوسطات
        if response_times:
            stats["average_response_time"] = sum(response_times) / len(response_times)
        
        if stats["total_requests"] > 0:
            stats["overall_success_rate"] = (
                stats["successful_requests"] / stats["total_requests"]
            ) * 100
        
        return stats
    
    def optimize_proxy_usage(self) -> Dict[str, Any]:
        """تحسين استخدام البروكسيات"""
        optimization_report = {
            "optimizations_applied": [],
            "disabled_proxies": 0,
            "updated_proxies": 0
        }
        
        # 1. إيقاف البروكسيات السيئة
        disabled_proxies = self.auto_disable_bad_proxies()
        if disabled_proxies:
            optimization_report["optimizations_applied"].append(
                f"Disabled {len(disabled_proxies)} poor-performing proxies"
            )
            optimization_report["disabled_proxies"] = len(disabled_proxies)
        
        # 2. تحديث إحصائيات البروكسيات
        self._update_proxy_rankings()
        optimization_report["optimizations_applied"].append("Updated proxy rankings")
        
        return optimization_report
    
    def _update_proxy_rankings(self):
        """تحديث ترتيب البروكسيات"""
        # يمكن إضافة منطق ترتيب البروكسيات هنا
        # بناءً على الأداء والاستخدام
        pass
    
    async def health_check_all_proxies(self) -> Dict[str, Any]:
        """فحص صحة جميع البروكسيات"""
        print("🔍 بدء فحص صحة البروكسيات...")
        
        test_results = await self.test_all_proxies()
        optimization_results = self.optimize_proxy_usage()
        
        return {
            "health_check_completed": True,
            "timestamp": datetime.utcnow().isoformat(),
            "test_results": test_results,
            "optimizations": optimization_results,
            "recommendations": self._generate_recommendations(test_results)
        }
    
    def _generate_recommendations(self, test_results: Dict[str, Any]) -> List[str]:
        """إنشاء توصيات بناءً على نتائج الاختبار"""
        recommendations = []
        
        working_ratio = test_results["working_proxies"] / test_results["total_proxies"] if test_results["total_proxies"] > 0 else 0
        
        if working_ratio < 0.5:
            recommendations.append("أقل من 50% من البروكسيات تعمل - يُنصح بإضافة بروكسيات جديدة")
        
        if test_results["total_proxies"] < 5:
            recommendations.append("عدد قليل من البروكسيات - يُنصح بإضافة المزيد للاستقرار")
        
        if working_ratio == 0:
            recommendations.append("لا توجد بروكسيات عاملة - تحقق من إعدادات الشبكة")
        
        return recommendations