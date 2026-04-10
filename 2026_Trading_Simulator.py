import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def call_gemini_stable(prompt):
    # استخدام رابط الإصدار 1.5 flash مع المفتاح مباشرة
    # تم تغيير الرابط لصيغة v1beta للتأكد من التوافق مع المفاتيح المجانية
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    try:
        print("🔗 محاولة الربط عبر الرابط المتوافق...")
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            # طباعة الخطأ كاملاً لفهمه
            return f"❌ خطأ {response.status_code}: {response.text[:100]}"
    except Exception as e:
        return f"❌ فشل تقني: {str(e)}"

def run_simulation():
    print("🚀 إطلاق نسخة التصحيح V7.1")
    market_context = "حلل وضع عملة SOL حالياً كخبير استثمار."
    analysis = call_gemini_stable(market_context)
    
    print(f"🏁 النتيجة: {analysis}")
    
    if TELEGRAM_TOKEN and "❌" not in analysis:
        msg = f"🧠 *نظام أسامة - تحديث V7.1*\n\n{analysis}"
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"})

if __name__ == "__main__":
    run_simulation()