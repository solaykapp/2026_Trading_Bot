import os
import time
import requests
from google import genai
from dotenv import load_dotenv

# تحميل الإعدادات
load_dotenv(override=True)

# المفاتيح (سيسحبها من Render Environment أو .env المحلي)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
RENDER_API_KEY = os.getenv("RENDER_API_KEY")
SERVICE_ID = os.getenv("SERVICE_ID")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
MODEL_ID = "gemini-3.1-flash-lite-preview"

def send_telegram_msg(message):
    """وظيفة إرسال الرسائل إلى تيليجرام"""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ تنبيه: بيانات تيليجرام غير مكتملة.")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"❌ خطأ في إرسال تيليجرام: {e}")

def get_render_events():
    url = f"https://api.render.com/v1/services/{SERVICE_ID}/events?limit=5"
    headers = {"Authorization": f"Bearer {RENDER_API_KEY}", "Accept": "application/json"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            events = response.json()
            if not events: return "السجل نظيف حالياً."
            summary = "📊 آخر أحداث السيرفر:\n"
            for item in events:
                event_data = item.get('event', item)
                summary += f"- {event_data.get('type')} @ {event_data.get('createdAt')[:16]}\n"
            return summary
        return f"تنبيه Render: {response.status_code}"
    except:
        return "خطأ في جلب البيانات."

def run_governance_bot():
    print("🚀 نظام الحوكمة V10 - تفعيل التنبيهات اللحظية")
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    while True:
        try:
            actual_data = get_render_events()
            prompt = f"حلل حالة السيرفر التالية باختصار وقدم نصيحة: {actual_data}"
            
            response = client.models.generate_content(model=MODEL_ID, contents=prompt)
            analysis = response.text
            
            # طباعة في اللوج (للمراقبة)
            print(f"💡 تحليل جديد: {analysis[:50]}...")
            
            # الإرسال إلى تيليجرام (الإضافة الجديدة)
            telegram_text = f"🛡️ *تقرير الحوكمة الذكي*\n\n{analysis}"
            send_telegram_msg(telegram_text)
            
            time.sleep(300) # فحص كل 5 دقائق لتقليل استهلاك الرسائل
        except Exception as e:
            print(f"⚠️ خطأ: {e}")
            time.sleep(60)

if __name__ == "__main__":
    run_governance_bot()