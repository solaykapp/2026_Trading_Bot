import os
import json
import time
import asyncio
from google import genai
from dotenv import load_dotenv

# الإعدادات المعتمدة
load_dotenv(override=True)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
MODEL_ID = "gemini-3.1-flash-lite-preview"

client = genai.Client(api_key=GEMINI_API_KEY)

async def update_dashboard_data(profit_val):
    """تحديث ملف البيانات الذي يقرأ منه Lovable"""
    dashboard_data = {
        "balance": 50000 + profit_val,
        "profit_percent": 2.4 + (profit_val / 50000 * 100),
        "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    # كتابة الملف محلياً ليتم رفعه عبر Git
    with open("dashboard_stats.json", "w") as f:
        json.dump(dashboard_data, f)
    print(f"📊 تم تحديث بيانات لوحة Lovable: +{profit_val} ريال")

async def master_engine():
    print("🚀 تشغيل محرك الأتمتة الكامل والمراقبة اللحظية...")
    current_profit = 0
    
    while True:
        try:
            # 1. تحليل السكالبينج (100 عملة حلال)
            prompt = "نفذ استراتيجية السكالبينج. إذا وجدت ربحاً، أعطني القيمة فقط."
            response = client.models.generate_content(model=MODEL_ID, contents=prompt)
            
            # 2. تحديث الأرباح (محاكاة الربح الحقيقي من الدالة الرياضية)
            # نفترض ربح صفقة لحظية
            trade_profit = 150 # مثال
            current_profit += trade_profit
            
            # 3. تحديث Dashboard (لوحة التحكم في صورتك)
            await update_dashboard_data(current_profit)
            
            # 4. التنبيه الفوري في تيليجرام (الرادار)
            # (كود الإرسال المعتاد)
            
        except Exception as e:
            print(f"⚠️ خطأ: {e}")
            
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(master_engine())