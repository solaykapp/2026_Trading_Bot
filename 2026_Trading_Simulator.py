import os, time, pandas as pd, requests
from dotenv import load_dotenv
from binance.client import Client
from ta.momentum import RSIIndicator
load_dotenv()
c = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))
def run_bot():
    print('🚀 البوت بدأ العمل...')
    while True:
        try:
            for s in ['BTCUSDT', 'ETHUSDT', 'SUIUSDT', 'SOLUSDT']:
                k = c.get_klines(symbol=s, interval='15m', limit=50)
                df = pd.DataFrame(k)[4].astype(float)
                r = RSIIndicator(close=df).rsi().iloc[-1]
                print(f'🔍 {s}: {r:.2f}')
                if r <= 42:
                    url = f'https://api.telegram.org/bot{os.getenv("TELEGRAM_TOKEN")}/sendMessage'
                    requests.post(url, json={'chat_id': os.getenv("TELEGRAM_CHAT_ID"), 'text': f'🎯 {s} RSI: {r:.2f}'})
            time.sleep(180)
        except Exception as e:
            print(f'Error: {e}'if __name__ == '__main__':
    run_bot()