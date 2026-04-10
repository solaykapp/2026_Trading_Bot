import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

# الإعدادات
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def call_gemini_direct(prompt):
    """الاتصال المباشر بـ Gemini v1 وتجاوز v1beta نهائياً"""
    # رابط الإصدار المستقر v1 (وليس v1beta)
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 800
        }
    }

    try:
        print("🔗 محاولة الاتصال المباشر ببروتوكول V1 المستقر...")
        response = requests.post(url, headers=headers, json=payload)
        response_data = response.json()
        
        if response.status_code == 200:
            return response_data['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"❌ خطأ API ({response.status_code}): {response.text}"
    except Exception as e:
        return f"❌ فشل الاتصال المباشر: {str(e)}"

def send_telegram(text):
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"})

def run_simulation():
    print("🚀 إطلاق نظام أسامة V7.0 (Direct Link)")
    
    market_context = "SOL/USDT السعر 145$، RSI 31. حلل كمدير محفظة حلال."
    analysis = call_gemini_direct(market_context)
    
    print(f"✅ النتيجة: {analysis[:50]}...")
    send_telegram(f"🧠 *نظام أسامة V7.0 - الربط المباشر*\n\n{analysis}")

if __name__ == "__main__":
    if not GEMINI_KEY:
        print("❌ المفتاح مفقود!")
    else:
        run_simulation()