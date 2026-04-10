import os, time, pandas as pd, requests; from dotenv import load_dotenv; from binance.client import Client; from ta.momentum import RSIIndicator; load_dotenv(); c=Client(os.getenv('BINANCE_API_KEY'),os.getenv('BINANCE_API_SECRET')); def run_bot(): print('🚀 البوت انطلق...'); t=os.getenv('TELEGRAM_TOKEN'); cid=os.getenv('TELEGRAM_CHAT_ID');
    while True:
        try:
            for s in ['BTCUSDT','ETHUSDT','SUIUSDT','SOLUSDT','AVAXUSDT']:
                k=c.get_klines(symbol=s,interval='15m',limit=50); df=pd.DataFrame(k)[4].astype(float); rsi=RSIIndicator(close=df).rsi().iloc[-1]; print(f'🔍 {s}: {rsi:.2f}');
                if rsi<=42: requests.post(f'https://api.telegram.org/bot{t}/sendMessage',json={'chat_id':cid,'text':f'🎯 {s} RSI: {rsi:.2f}'})
            time.sleep(180)
        except Exception as e: print(f'Err: {e}'); time.sleep(60)
if __name__=='__main__': run_bot()
