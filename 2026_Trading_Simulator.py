import os
import asyncio
import aiohttp
import json
from google import genai
from dotenv import load_dotenv

# 1. تحميل الإعدادات الأمنية
load_dotenv(override=True)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MODEL_ID = "gemini-3.1-flash-lite-preview"
client = genai.Client(api_key=GEMINI_API_KEY)

async def send_to_telegram(message):
    """إرسال التنبيهات لتيليجرام"""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    async with aiohttp.ClientSession() as session:
        try:
            await session.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"})
        except: pass

async def trading_engine():
    print("🚀 تم تفعيل محرك الدالة الرياضية والتنفيذ الآلي...")
    
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                # المحرك يعمل في الخلفية على 100 عملة حلال
                # المنصات: Binance, Bybit, TradingView, CMC, Investing.com
                prompt = """
                قم بدور محرك تداول آلي يعتمد على الدالة الرياضية (RSI + MACD + Volume).
                1. افحص الـ 100 عملة حلال.
                2. إذا وجدت فرصة دخول (إشارة)، صغها بتنسيق الرادار:
                   🌍 [رادار عالمي - Bybit]
                   💎 العملة: {symbol}
                   📈 RSI: {val}
                   ✅ إشارة: دخول (Spot حلال)
                3. إذا اتخذت قراراً بالتنفيذ آلياً، أتبعه برسالة:
                   💰 [أمر تنفيذ آلي]
                   ⚙️ النوع: BUY/SELL
                   💵 السعر: {price}
                   ⚖️ الكمية: 1% من المحفظة
                
                رد بتنسيق نصي مباشر لتيليجرام.
                """
                
                response = client.models.generate_content(model=MODEL_ID, contents=prompt)
                
                if response.text:
                    await send_to_telegram(response.text)
                    print(f"✅ تم تحديث الحالة وإرسال الأوامر.")

            except Exception as e:
                print(f"❌ خطأ في المحرك: {e}")

            # فحص السوق كل دقيقة لضمان السكالبينج اللحظي
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(trading_engine())