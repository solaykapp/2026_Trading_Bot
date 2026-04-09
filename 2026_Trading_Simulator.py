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
        try:
            requests.post(url, json={"chat_id": chat_id, "text": msg})
        except: pass

try:
    client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))
    print("✅ تم الاتصال ببينانس بنجاح")
except Exception as e:
    print(f"❌ خطأ في الاتصال: {e}")

def run_bot():
    rsi_threshold = 42 
    start_msg = "🤖 [ML-V2] المحرك الذكي المصحح يعمل الآن بنجاح!"
    print(start_msg)
    send_telegram(start_msg)
    
    while True:
        try:
            symbols = ['BTCUSDT', 'ETHUSDT', 'SUIUSDT', 'SOLUSDT',      klines = client.get_klines(symbol=symbol, interval='15m', limit=50)
                df = pd.DataFrame(klines)
                close_prices = df[4].astype(float)
                rsi = RSIIndicator(close=close_prices).rsi().iloc[-1]
                
                print(f"🔍 فحص {symbol} | RSI: {rsi:.2f}")
                
                if rsi <= rsi_threshold:
                    msg = f"🎯 فرصة هجومية: {symbol}\n📈 RSI: {rsi:.2f}\n⏰ {time.ctime()}"
                    send_telegram(msg)
            
            time.sleep(180)
        except Exception as e:
            print(f"🔄 محاولة تصحيح ذاتي: {e}")
            time.sleep(60)

if __name__ == "__main__":
    run_bot()
