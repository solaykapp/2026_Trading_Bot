import os, time, pandas as pd, requests
from dotenv import load_dotenv
from binance.client import Client
from ta.momentum import RSIIndicator

# 1. تحميل الإعدادات من ملف .env
load_dotenv()

def send_telegram(msg):
    """وظيفة إرسال التنبيهات إلى تليجرام"""
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            requests.post(url, json={'chat_id': chat_id, 'text': msg})
        except Exception as e:
            print(f"❌ خطأ تليجرام: {e}")

# 2. إعداد اتصال بينانس
try:
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    client = Client(api_key, api_secret)
    print("✅ نظام بينانس متصل بنجاح")
except Exception as e:
    print(f"❌ فشل الاتصال ببينانس: {e}")

def run_trading_bot():
    """المحرك الرئيسي لفحص السوق"""
    print("🚀 المحرك V2.5 يعمل الآن... جاري مراقبة العملات")
    send_telegram("🤖 [V2.5] تم تفعيل الرادار الهجومي بنجاح!")
    
    # قائمة العملات المستهدفة
    symbols = ['BTCUSDT', 'ETHUSDT', 'SUIUSDT', 'SOLUSDT', 'AVAXUSDT']
    
    while True:
        try:
            for symbol in symbols:
                # جلب آخر 50 شمعة (إطار 15 دقيقة)
                klines = client.get_klines(symbol=symbol, interval='15m', limit=50)
                
                # تحويل البيانات إلى DataFrame لاستخراج سعر الإغلاق
                df = pd.DataFrame(klines)[4].astype(float)
                
                # حساب مؤشر RSI
                rsi_val = RSIIndicator(close=df).rsi().iloc[-1]
                
                # طباعة النتيجة في Terminal للمراقبة المحلية
                print(f"🔍 {symbol}: {rsi_val:.2f}")
                
                # شرط التنبيه: إذا كان RSI أقل من أو يساوي 42
                if rsi_val <= 42:
                    alert = (
                        f"🎯 فرصة هجومية اكتشفت! \n"
                        f"🪙 العملة: {symbol}\n"
                        f"📈 RSI الحالي: {rsi_val:.2f}\n"
                        f"⏰ الوقت: {time.strftime('%H:%M:%S')}"
                    )
                    send_telegram(alert)
            
            # انتظار 3 دقائق قبل الفحص التالي
            time.sleep(180)
            
        except Exception as e:
            print(f"🔄 حدث خطأ، إعادة محاولة تلقائية بعد دقيقة: {e}")
            time.sleep(60)

# 3. نقطة انطلاق البرنامج
if __name__ == "__main__":
    run_trading_bot()