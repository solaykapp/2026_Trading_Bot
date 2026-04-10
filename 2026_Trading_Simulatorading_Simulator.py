import os, time, pandas as pd, requests; from dotenv import load_dotenv; from binance.client import Client; from ta.momentum import RSIIndicator; load_dotenv(); client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET')); def run_bot(): print('🚀 [V2.2] المحرك الهجومي بدأ...'); token=os.getenv('TELEGRAM_TOKEN'); chat_id=os.getenv('TELEGRAM_CHAT_ID');
    while True:
        try:
            for s in ['BTCUSDT', 'ETHUSDT', 'SUIUSDT', 'SOLUSDT', 'AVAXUSDT']:
                k = client.get_klines(symbol=s, interval='15m', limit=50); df = pd.DataFrame(k)[4].astype(float); rsi = RSIIndicator(close=df).rsi().iloc[-1]; print(f'🔍 {s}: {rsi:.2f}');
                if rsi <= 42: requests.post(f'https://api.telegram.org/bot{token}/sendMessage', json={'chat_id': chat_id, 'text': f'🎯 {s} RSI: {rsi:.2f}'})
            time.sleep(180)
        except Exception as e: print(f'Err: {e}'); time.sleep(60)
if __name__ == '__main__': run_bot()
