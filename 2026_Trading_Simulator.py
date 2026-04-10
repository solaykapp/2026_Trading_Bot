import os
import requests
import google.generativeai as genai
from dotenv import load_dotenv

# 1. تحميل الإعدادات المحلية (إذا وجدت)
load_dotenv()

# 2. جلب المفاتيح من بيئة العمل (Render أو .env)
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 3. تهيئة محرك Gemini (مع تصحيح اسم الموديل لتجنب خطأ 404)
if GEMINI_KEY:
    try:
        genai.configure(api_key=GEMINI_KEY)
        # استخدام الاسم المباشر للموديل لضمان التوافق
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction=(
                "أنت مدير محفظة أسامة بن عبد الرحمن الاستثمارية. "
                "رأس المال المخصص: 50,000 ريال سعودي. "
                "قاعدة العمل: الاستثمار الحلال فقط، إدارة مخاطر صارمة، "
                "وتحليل تقني دقيق بناءً على المؤشرات المزودة."
            )
        )
        print("✅ تم تهيئة Gemini بنجاح.")
    except Exception as e:
        print(f"❌ فشل في تهيئة Gemini: {str(e)}")
else:
    print("❌ خطأ: مفتاح GEMINI_API_KEY غير موجود في إعدادات البيئة!")

def send_telegram_msg(text):
    """إرسال التحديثات مباشرة لهاتف أسامة"""
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
        try:
            requests.post(url, json=payload)
        except Exception as e:
            print(f"❌ خطأ في إرسال تليجرام: {str(e)}")

def analyze_market_live():
    """محاكاة فرصة سوقية لاختبار الربط"""
    print("🔄 جاري فحص السوق والربط مع Gemini...")
    
    # مثال لبيانات قادمة من الرادار
    market_snapshot = (
        "الرمز: SOL/USDT\n"
        "السعر الحالي: 145.2\n"
        "مؤشر RSI: 32 (تشبع بيعي)\n"
        "الاتجاه: صاعد على الفاصل الزمني 4H"
    )
    
    try:
        # طلب التحليل من Gemini
        prompt = f"حلل هذه الفرصة لأسامة وفق معاييرنا: {market_snapshot}"
        response = model.generate_content(prompt)
        analysis = response.text
        
        # إرسال النتيجة لتليجرام
        final_msg = f"🧠 *اختبار الربط الذكي - V5.8*\n\n{analysis}"
        send_telegram_msg(final_msg)
        
        return analysis
    except Exception as e:
        error_msg = f"❌ خطأ في التحليل: {str(e)}"
        print(error_msg)
        return error_msg

if __name__ == "__main__":
    # تشغيل الاختبار مرة واحدة عند الإقلاع للتأكد من الربط
    result = analyze_market_live()
    print(f"✅ نتيجة التحليل النهائي: {result}")