import os
import requests
import google.generativeai as genai
from dotenv import load_dotenv

# 1. تحميل الإعدادات المحلية
load_dotenv()

# 2. جلب المفاتيح من إعدادات البيئة
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

model = None

print("🚀 جاري بدء تشغيل النظام ببروتوكول V6.4 المستقر...")

if GEMINI_KEY:
    try:
        # التعديل الحاسم: فرض بروتوكول 'rest' لتجاوز مشاكل الإصدارات التجريبية v1beta
        genai.configure(api_key=GEMINI_KEY, transport='rest')
        
        # اختيار الموديل المستقر الأكثر كفاءة
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction=(
                "أنت مدير محفظة أسامة بن عبد الرحمن الاستثمارية. "
                "تحلل البيانات وتتخذ قرارات تداول بناءً على الحوكمة وإدارة المخاطر. "
                "لغة التواصل: العربية."
            )
        )
        # اختبار أولي سريع للتأكد من تفعيل الربط
        test_check = model.generate_content("ping")
        print("✅ تم تفعيل الموديل والربط بنجاح عبر بروتوكول REST.")
    except Exception as e:
        print(f"❌ فشل الربط النهائي. السبب: {str(e)}")
else:
    print("❌ خطأ: GEMINI_API_KEY غير موجود في إعدادات Render!")

def send_telegram_msg(text):
    """إرسال التقارير لتليجرام أسامة"""
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
        try:
            requests.post(url, json=payload)
        except Exception as e:
            print(f"❌ فشل إرسال تليجرام: {str(e)}")

def analyze_market_live():
    """محاكاة فرصة تداول حقيقية لأسامة"""
    if not model:
        return "❌ محرك الذكاء الاصطناعي غير جاهز."

    market_data = (
        "العملة: SOL/USDT\n"
        "السعر الحالي: 145.20$\n"
        "مؤشر RSI: 31 (تشبع بيعي)\n"
        "المعايير: حوكمة شرعية + إدارة مخاطر"
    )
    
    try:
        # طلب التحليل الذكي
        prompt = f"حلل هذه الفرصة لأسامة وقدم نصيحة استثمارية: {market_data}"
        response = model.generate_content(prompt)
        analysis = response.text
        
        # إرسال التحديث لهاتفك
        final_msg = f"🧠 *نظام أسامة الذكي - V6.4*\n\n{analysis}"
        send_telegram_msg(final_msg)
        return analysis
    except Exception as e:
        return f"❌ خطأ أثناء التحليل: {str(e)}"

if __name__ == "__main__":
    # تنفيذ المحاكاة الأولى فور التشغيل
    print("🔄 جاري توليد أول تحليل استثماري...")
    result = analyze_market_live()
    print(f"🏁 النتيجة النهائية: {result}")