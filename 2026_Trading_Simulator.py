import os, time, pandas as pd, requests
from dotenv import load_dotenv
from binance.client import Client
from ta.momentum import RSIIndicator

load_dotenv()

def send_tg(m):
    t = os.getenv('TELEGRAM_TOKEN')
    c = os.getenv('TELEGRAM_CHAT_ID')
    if t and c:
        requests.post(f'https://api.telegram.org/bot{t}/sendMessage', json={'chat_id': c, 'text': m})

try:
    client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))
except Exception as e:
    print(f'Conn Error: {e}')

def run():
    print('🚀 المحرك الذكي V2.3 انطلق...')
    send_tg('🤖 تم تفعيل المحرك الهجومي V2.3 بنجاح!')
    while True:
        try:
            for s in ['BTCUSDT', 'ETHUSDT', 'SUIUSDT', 'SOLUSDT', 'AVAXUSDT']:
                k = client.get_klines(symbol=s rsi = RSIIndicator(close=df).rsi().iloc[-1]
                print(f'🔍 {s}: {rsi:.2f}')
                if rsi <= 42:
                    send_tg(f'🎯 فرصة: {s} | RSI: {rsi:.2f}')
            time.sleep(180)
        except Exception as e:
            print(f'Err: {e}')
            time.sleep(60)

if __name__ == '__main__':
    run()