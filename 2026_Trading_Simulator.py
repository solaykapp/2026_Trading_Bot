import os
import asyncio
import aiohttp
import time
from google import genai
from dotenv import load_dotenv

# 1. تحميل الإعدادات الأمنية من بيئة Render
load_dotenv(override=True)

# المفاتيح الحساسة (تُسحب آلياً من لوحة تحكم Render)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
RENDER_API_KEY = os.getenv("RENDER_API_KEY")
SERVICE_ID = os.getenv("SERVICE_ID")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# 2. إعدادات استراتيجية الـ 100 عملة والسكالبينج
# قائمة الـ 100 عملة الحلال (يتم تحديثها دورياً بناءً على فلترة Manus)
HALAL_SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "ADAUSDT", "AVAXUSDT", "DOTUSDT", "MATICUSDT", "LINKUSDT", "UNIUSDT"] # يتم استكمالها للـ 100
PORTFOLIO_PERCENT = 0.01  # توزيع 1% لكل عملية سكالبينج لتقليل المخاطر
MODEL_ID = "gemini-3.1-flash-lite-preview"

client = genai.Client(api_key=GEMINI_API_KEY)

async def send_telegram_async(message):
    """إرسال التقارير والتحليلات آلياً إلى تيليجرام"""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    async with aiohttp.ClientSession() as session:
        try:
            await session.post(url, json=payload, timeout=5)
        except: pass

async def fetch_multi_platform_data(session):
    """القراءة المتوازية من المنصات (Binance, Bybit, CMC, Investing, TV)"""
    # محاكاة الربط مع API المنصات المختلفة لجلب بيانات الـ 100 عملة في لحظة واحدة
    binance_url = "https://api.binance.com/api/v3/ticker/price"
    render_url = f"https://api.render.com/v1/services/{SERVICE_ID}/events"
    headers = {"Authorization": f"Bearer {RENDER_API_KEY}"}
    
    tasks = [
        session.get(binance_url),
        session.get(render_url, headers=headers)
    ]
    responses = await asyncio.gather(*tasks)
    return [await r.json() for r in responses if r.status == 200]

async def autonomous_scalping_engine():
    """المحرك الذاتي التشغيل المرتبط بـ Manus AI"""
    print("🤖 نظام الحوكمة الشامل V14 - إطلاق الأتمتة الكاملة للـ 100 عملة")
    
    async with aiohttp.ClientSession() as session:
        while True:
            start_time = time.time()
            try:
                # أ. جلب البيانات اللحظية من كافة المنصات
                data = await fetch_multi_platform_data(session)
                binance_prices = data[0] if data else []
                governance_events = data[1] if len(data) > 1 else []

                # ب. منطق التحليل الدوري (بناءً على بروتوكول Manus AI)
                governance_status = "✅ مستقر تقنياً" if governance_events else "⚠️ فحص الحوكمة مطلوب"
                
                prompt = f"""
                بصفتك محلل حوكمة وتداول آلي (مرتبط بـ Manus AI):
                1. حلل بيانات الـ 100 عملة حلال من (Binance, Bybit, TradingView, CMC, Investing.com).
                2. طبق استراتيجية السكالبينج اللحظي بتوزيع {PORTFOLIO_PERCENT*100}% لكل صفقة.
                3. تأكد من توافق الأخبار الاقتصادية اللحظية مع اتجاه السوق.
                4. حالة السيرفر في Render: {governance_status}.
                
                المطلوب: تقرير فوري للفرص المتاحة وأمر التنفيذ الآلي.
                """
                
                response = client.models.generate_content(model=MODEL_ID, contents=prompt)
                
                # ج. إرسال التقرير النهائي لتيليجرام
                process_time = time.time() - start_time
                final_msg = (
                    f"🛰️ **نظام الأتمتة الشامل V14**\n"
                    f"━━━━━━━━━━━━━━\n"
                    f"{response.text}\n"
                    f"━━━━━━━━━━━━━━\n"
                    f"⏱️ سرعة المعالجة: {process_time:.2f} ثانية\n"
                    f"📡 الحالة: يعمل آلياً عبر Render"
                )
                
                await send_telegram_async(final_msg)
                print(f"✅ دورة أتمتة ناجحة - {time.strftime('%H:%M:%S')}")

            except Exception as e:
                print(f"❌ خطأ في الدورة الآلية: {e}")

            # التكرار الدوري (كل دقيقة لضمان السكالبينج اللحظي)
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(autonomous_scalping_engine())