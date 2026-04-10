import os
import time
import requests
import google.generativeai as genai
from dotenv import load_dotenv

# 1. تفعيل قراءة ملف الأسرار .env
load_dotenv()

# 2. استدعاء المفاتيح بأمان
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 3. تهيئة العقل الذكي
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    system_instruction="أنت مدير محفظة أسامة للاستثمار الحلال. حلل البيانات واتخذ قرار BUY أو WAIT بناءً على معايير الحوكمة."
)

def analyze_market_live():
    # محاكاة لبيانات حقيقية وصلت من الرادار
    market_snapshot = "Symbol: SOL/USDT, Price: 145.2, RSI: 32, Source: DexScreener"
    
    try:
        response = model.generate_content(f"حلل هذه الفرصة لأسامة: {market_snapshot}")
        analysis = response.text
        
        # إرسال النتيجة لتليجرام للتأكد من الربط
        msg = f"🧠 *اختبار الربط الذكي مع Gemini*\n\n{analysis}"
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
        
        return analysis
    except Exception as e:
        return f"خطأ في الربط: {str(e)}"

if __name__ == "__main__":
    print("🔄 جاري فحص الربط مع Gemini...")
    result = analyze_market_live()
    print(f"✅ نتيجة التحليل الذكي: {result}")