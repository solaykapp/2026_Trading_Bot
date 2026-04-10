import os
import requests
import google.generativeai as genai
from dotenv import load_dotenv

# 1. تحميل الإعدادات المحلية للعمل على الماك
load_dotenv()

# 2. جلب المفاتيح من إعدادات البيئة (Render Environment Variables)
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 3. نظام اختيار الموديل الذكي لتجاوز خطأ 404
model = None
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    
    # قائمة الموديلات المتاحة للربط البرمجي
    model_candidates = ['gemini-1.5-flash-latest', 'gemini-1.5-flash', 'gemini-pro']
    
    for m_name in model_candidates:
        try:
            print(f"🔄 جاري محاولة الربط مع الموديل: {m_name}...")
            temp_model = genai.GenerativeModel(
                model_name=m_name,
                system_instruction=(
                    "أنت مدير محفظة أسامة بن عبد الرحمن الاستثمارية. "
                    "تحلل السوق بناءً على معايير الحوكمة الشرعية وإدارة المخاطر الصارمة. "
                    "لغة التواصل: العربية الاحترافية."
                )
            )
            # اختبار الموديل بطلب بسيط للتأكد من استجابته
            temp_model.generate_content("ping")
            model = temp_model
            print(f"✅ تم تفعيل الموديل بنجاح: {m_name}")
            break
        except Exception as e:
            print(f"⚠️ الموديل {m_name} غير متاح حالياً. الانتقال للبديل...")
else:
    print("❌ خطأ: مفتاح GEMINI_API_KEY غير موجود في إعدادات Render!")

def send_telegram_msg(text):
    """إرسال التقارير مباشرة لتليجرام أسامة"""
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
        try:
            requests.post(url, json=payload)
        except Exception as e:
            print(f"❌ خطأ في إرسال تليجرام: {str(e)}")

def analyze_market_live():
    """محاكاة تحليل سوقي لعملة SOL/USDT"""
    if not model:
        return "❌ لم يتم تهيئة أي موديل ذكاء اصطناعي بنجاح."

    market_snapshot = (
        "العملة: SOL/USDT\n"
        "السعر: 145.20$\n"
        "RSI: 31 (قريب من منطقة الشراء)\n"
        "الحالة: ارتداد من منطقة دعم قوية"
    )
    
    try:
        # طلب التحليل من الموديل الذي تم تفعيله
        prompt = f"قدم تحليل سريع وتوصية لأسامة بناءً على هذه البيانات: {market_snapshot}"
        response = model.generate_content(prompt)
        analysis = response.text
        
        # إرسال النتيجة النهائية لتليجرام
        final_msg = f"🧠 *نظام التداول الذكي لأسامة - V6.1*\n\n{analysis}"
        send_telegram_msg(final_msg)
        
        return analysis
    except Exception as e:
        err_msg = f"❌ خطأ أثناء توليد التحليل: {str(e)}"
        print(err_msg)
        return err_msg

if __name__ == "__main__":
    # تشغيل البوت للتأكد من الربط فوراً
    print("🚀 جاري بدء تشغيل النظام...")
    result = analyze_market_live()
    print(f"🏁 نتيجة التشغيل: {result}")