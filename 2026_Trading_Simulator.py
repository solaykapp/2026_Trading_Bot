import os, time, pandas as pd, requests
from dotenv import load_dotenv
from binance.client import Client
from ta.momentum import RSIIndicator

load_dotenv()

def send_telegram(msg):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try: requests.post(url, json={"chat_id": chat_id, "text": msg})
        except: pass

try:
    client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))
    print("✅ المتداول الذكي متصل ببينانس")
except Exception as e:
    print(f"❌ خطأ اتصال: {e}")

def run_bot():
    print("🚀 تم تشغيل المحرك الهجومي V2...")
    send_telegram("🤖 [ML-V2] النظام متصل ويعمل الآن بكامل طاقته!")
    
    while True:
        try:
            symbols = ['BTCUSDT', 'ETHUSDT', 'SUIUSDT', 'SOLUSDT', 'AVAXUSDT']
        '15m', limit=50)
                df = pd.DataFrame(k)[4].astype(float)
                rsi = RSIIndicator(close=df).rsi().iloc[-1]
                print(f"🔍 {symbol}: {rsi:.2f}")
                
                if rsi <= 42:
                    send_telegram(f"🎯 فرصة: {symbol}\n📈 RSI: {rsi:.2f}")
            time.sleep(180)
        except Exception as e:
            print(f"🔄 تنبيه: {e}")
            time.sleep(60)

if __name__ == "__main__":
    run_bot()
