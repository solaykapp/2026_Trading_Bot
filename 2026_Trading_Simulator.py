import os
import time
import requests
from google import genai
from dotenv import load_dotenv

# تحميل الإعدادات
load_dotenv(override=True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
RENDER_API_KEY = os.getenv("RENDER_API_KEY")
SERVICE_ID = os.getenv("SERVICE_ID")
MODEL_ID = "gemini-3.1-flash-lite-preview"

def get_render_events():
    url = f"https://api.render.com/v1/services/{SERVICE_ID}/events?limit=5"
    headers = {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Accept": "application/json"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            events = response.json()
            
            # إذا كان السجل فارغاً
            if not events or len(events) == 0:
                return "لا توجد أحداث مسجلة حالياً في السيرفر (السجل نظيف)."

            # استخراج البيانات بأمان
            summary = "آخر أحداث السيرفر المستخرجة:\n"
            for item in events:
                # استخدام .get() مع قيمة افتراضية لتجنب خطأ الـ Key
                event_data = item.get('event', item) # بعض استجابات ريندر تضع البيانات داخل كائن 'event'
                e_type = event_data.get('type', 'نشاط غير محدد')
                e_time = event_data.get('createdAt', 'وقت غير معروف')
                summary += f"- {e_type} @ {e_time}\n"
            return summary
        else:
            return f"تنبيه: Render استجاب برمز {response.status_code}"
    except Exception as e:
        return f"خطأ في معالجة البيانات: {str(e)}"

def run_governance_bot():
    print("🚀 نظام الحوكمة V9.2 - متصل ومؤمن")
    
    if not GEMINI_API_KEY or not RENDER_API_KEY:
        print("❌ خطأ: تأكد من تعبئة المفاتيح في ملف .env")
        return

    client = genai.Client(api_key=GEMINI_API_KEY)
    
    try:
        while True:
            t = time.strftime('%H:%M:%S')
            print(f"\n[{t}] 📡 جاري فحص الحالة في فرانكفورت...")
            
            actual_data = get_render_events()
            print(f"📦 البيانات المستلمة: {actual_data[:100]}...") # طباعة مختصرة للتأكد
            
            prompt = f"""
            بصفتك مستشار حوكمة تقنية، حلل حالة سيرفر Render التالية:
            {actual_data}
            
            المطلوب: تقييم الاستقرار وتقديم نصيحة واحدة.
            """
            
            try:
                response = client.models.generate_content(model=MODEL_ID, contents=prompt)
                print(f"💡 التحليل الذكي:\n{response.text}")
            except Exception as ge:
                print(f"⚠️ فشل تحليل Gemini: {ge}")

            print("="*50)
            time.sleep(120)
            
    except KeyboardInterrupt:
        print("\n🛑 تم إيقاف المراقبة يدوياً.")

if __name__ == "__main__":
    run_governance_bot()