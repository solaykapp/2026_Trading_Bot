import os
import time
import requests
import google.generativeai as genai
from dotenv import load_dotenv

# إعداد البيانات الأساسية
GEMINI_KEY = "AIzaSyCnAg1KU-1bIBRsW2z63XLdSsZ1rHuyPy8"
TELEGRAM_TOKEN = "7625126838:AAHTL9j8_N7m6LOf-556O-L2N20K0Yy452c"
TELEGRAM_CHAT_ID = "8623422400"

# تهيئة Gemini AI
genai.configure(api_key=GEMINI_KEY)

# تعليمات النظام - العقل المدبر لأسامة
SYSTEM_PROMPT = """
أنت 'المدير المستقل لمحفظة أسامة'. 
مرجعك الوحيد والأساسي هو محادثة (الاستثمار الآلي في الأسواق الحلال): https://gemini.google.com/share/ddffe741e1a7

قواعدك الذهبية والملزمة:
1. الفلترة الشرعية: استبعاد أي عملة (قمار، ربا، ميم مشبوه، مشاريع غير واضحة) قبل البدء بالتحليل.
2. إدارة المحفظة: رأس مال 50,000 ريال، الدخول بـ 133 دولار (ما يعادل 500 ريال) لكل عملية.
3. الذكاء التشغيلي: ادمج زخم DexScreener مع دقة TradingView والبيانات اللحظية لـ Binance/Bybit.
4. اتخاذ القرار: اتخذ قرار BUY فقط عندما تتجاوز ثقتك في النجاح 90%.
5. الهدف: النمو التدريجي والآمن للوصول للمليون بإذن الله.
"""

model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    system_instruction=SYSTEM_PROMPT
)

def analyze_and_decide(market_data):
    """وظيفة اتخاذ القرار الذكي"""
    prompt = f"حلل المعطيات التالية واتخذ قراراً استثمارياً: {market_data}"
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"WAIT | خطأ تقني: {str(e)}"

def send_telegram_notification(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"})

def autonomous_trading_engine():
    print("🚀 محرك الاستثمار الآلي الذكي يعمل الآن...")
    while True:
        # هنا يقوم البوت بجمع البيانات من المصادر الأربعة
        # مثال لبيانات مجمعة من الرادار
        market_snapshot = "Symbol: ARBUSDT, RSI: 42, Trend: Bullish, Source: Bybit & TradingView"
        
        analysis_result = analyze_and_decide(market_snapshot)
        
        if "BUY" in analysis_result.upper():
            final_msg = (
                f"🤖 *قرار استثماري ذكي*\n"
                f"✅ الحالة: شراء (BUY)\n"
                f"💰 المبلغ: $133.0\n"
                f"🧠 التحليل الذكي: {analysis_result}"
            )
            send_telegram_notification(final_msg)
        
        # الانتظار لمدة 10 دقائق قبل المسح التالي لضمان دقة الـ Scalping
        time.sleep(600)

if __name__ == "__main__":
    autonomous_trading_engine()