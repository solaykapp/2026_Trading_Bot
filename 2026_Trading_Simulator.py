import os
import requests
import google.generativeai as genai
from dotenv import load_dotenv

# تحميل الإعدادات المحلية (لجهاز الماك)
load_dotenv()

# جلب المفاتيح من Render Environment Variables
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

model = None

print("🔍 بدأت عملية التحقق من الاتصال...")

if GEMINI_KEY:
    try:
        genai.configure(api_key=GEMINI_KEY)
        # محاولة الوصول لأحدث الموديلات المستقرة
        model_candidates = ['gemini-1.5-flash-latest', 'gemini-1.5-flash', 'gemini-pro']
        
        for m_name in model_candidates:
            try:
                print(f"🔄 محاولة فحص الموديل: {m_name}")
                temp_model = genai.GenerativeModel(model_name=m_name)
                # اختبار حقيقي بطلب بسيط جداً
                test_response = temp_model.generate_content("Say OK")
                
                if test_response:
                    model = temp_model
                    print(f"✅ نجح الاتصال بـ: {m_name}")
                    break
            except Exception as inner_error:
                # هذا السطر سيكشف لنا في الـ Logs سبب الرفض (API Key expired, Permission denied, etc.)
                print(f"❌ الموديل {m_name} فشل بسبب: {str(inner_error)}")
                
    except Exception as e:
        print(f"❌ خطأ عام في تهيئة مكتبة Google: {str(e)}")
else:
    print("❌ خطأ: مفتاح GEMINI_API_KEY مفقود في إعدادات Render!")

def send_telegram_msg(text):
    """إرسال التقرير لتليجرام أسامة"""
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
        try:
            requests.post(url, json=payload)
        except Exception as e:
            print(f"❌ فشل إرسال تليجرام: {str(e)}")

def analyze_market_live():
    if not model:
        return "❌ النظام غير متصل بـ AI حالياً."

    market_data = "العملة: SOL/USDT | السعر: 145.20$ | RSI: 31"
    
    try:
        prompt = f"حلل البيانات التالية كخبير حوكمة استثمارية لأسامة: {market_data}"
        response = model.generate_content(prompt)
        analysis = response.text
        
        final_msg = f"🧠 *تحديث النظام الذكي - أسامة V6.2*\n\n{analysis}"
        send_telegram_msg(final_msg)
        return analysis
    except Exception as e:
        return f"❌ فشل توليد التحليل: {str(e)}"

if __name__ == "__main__":
    print("🚀 جاري إطلاق محرك التحليل...")
    result = analyze_market_live()
    print(f"🏁 النتيجة النهائية: {result}")