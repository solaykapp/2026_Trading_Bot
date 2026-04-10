import os, time, pandas as pd, requests
from dotenv import load_dotenv
from binance.client import Client
from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator

load_dotenv()

def send_telegram(msg):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try: requests.post(url, json={'chat_id': chat_id, 'text': msg})
        except: pass

try:
    client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))
    print("✅ نظام التحليل المتقدم متصل")
except Exception as e:
    print(f"❌ خطأ: {e}")

def run_advanced_bot():
    print("🚀 رادار الدقة العالية V3.0 انطلق...")
    send_telegram("🎯 تم تفعيل رادار الدقة العالية (RSI + MACD)")
    
    symbols = ['BTCUSDT', 'ETHUSDT', 'SUIUSDT', 'SOLUSDT', 'AVAXUSDT']
    
    while True:
        try:
            for symbol in symbols:
                klines = client.get_klines(symbol=symbol, interval='15m', limit=100)
                df = pd.DataFrame(klines)[4].astype(float)
                
                # 1. حساب RSI
                rsi = RSIIndicator(close=df).rsi().iloc[-1]
                
                # 2. حساب MACD
                macd_obj = MACD(close=df)
                macd_line = macd_obj.macd().iloc[-1]
                signal_line = macd_obj.macd_signal().iloc[-1]
                
                # 3. حساب المتوسط المتحرك EMA 200 (لمعرفة الاتجاه)
                ema_200 = EMAIndicator(close=df, window=100).ema_indicator().iloc[-1]
                current_price = df.iloc[-1]

                # الخوارزمية المطورة للدقة (الإشارة الذهبية):
                # شرط 1: RSI تحت 42 (سعر رخيص)
                # شرط 2: MACD يتقاطع صعوداً أو يقترب من الصفر (بداية زخم)
                # شرط 3: السعر ليس في انهيار حر تحت الـ EMA بشكل حاد
                
                if rsi <= 42 and macd_line > signal_line:
                    status = "🔥 إشارة قوية (تأكيد مزدوج)" if current_price > ema_200 else "⚠️ إشارة مضاربة (عكس الاتجاه)"
                    alert = (
                        f"{status}\n"
                        f"🪙 العملة: {symbol}\n"
                        f"📈 RSI: {rsi:.2f}\n"
                        f"📊 MACD: تقاطع إيجابي ✅\n"
                        f"⏰ {time.strftime('%H:%M:%S')}"
                    )
                    send_telegram(alert)
                    print(f"🎯 تم إرسال تنبيه عالي الدقة لـ {symbol}")
                else:
                    print(f"🔍 {symbol}: RSI {rsi:.2f} | لا يوجد تقاطع MACD")

            time.sleep(180)
        except Exception as e:
            print(f"🔄 إعادة محاولة: {e}"); time.sleep(60)

if __name__ == "__main__":
    run_advanced_bot()