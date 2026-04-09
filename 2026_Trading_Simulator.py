import os, time, pandas as pd, requests
from dotenv import load_dotenv
from binance.client import Client
from openai import OpenAI
from ta.momentum import RSIIndicator

load_dotenv()
client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))
ai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# استراتيجية ML-V2: تعديل آلي
def run_bot():
    rsi_threshold = 42 # هجومي مبدئي
    while True:
        try:
            symbols = ['BTCUSDT', 'ETHUSDT', 'SUIUSDT', 'SOLUSDT', 'AVAXUSDT']
            for symbol in symbols:
                klines = client.get_klines(symbol=symbol, interval='15m', limit=50)
                df = pd.DataFrame(klines)[4].astype(float)
                rsi = RSIIndicator(close=df).rsi().iloc[-1]
                
                if rsi <= rsi_threshold:
                    msg = f"🤖 [ML-V2] فرصة رصدت لـ {symbol} | RSI: {rsi:.2f}"
                    requests.post(f"https://api.tel)}/sendMessage", 
                                  json={"chat_id": os.getenv('TELEGRAM_CHAT_ID'), "text": msg})
                    # تسجيل البيانات للتعلم المستقبلي
                    pd.DataFrame([[time.ctime(), symbol, rsi, 'AUTO_ML']].to_csv('trading_data.csv', mode='a', index=False, header=False)
            time.sleep(180)
        except Exception as e:
            print(f"Self-Healing in progress: {e}")
            time.sleep(60)
