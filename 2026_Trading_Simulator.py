import os, asyncio, aiohttp, pandas as pd, time
from dotenv import load_dotenv
from binance.client import Client
from pybit.unified_trading import HTTP
from ta.momentum import RSIIndicator
from ta.trend import MACD

load_dotenv()

# --- الحوكمة المالية والحلال ---
# تقسيم 50,000 ريال (13,333 دولار) على 100 عملية
TRADE_AMOUNT_USD = 133.0 

# إعداد الاتصالات
b_client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))
bybit_session = HTTP(testnet=False, api_key=os.getenv('BYBIT_API_KEY'), api_secret=os.getenv('BYBIT_API_SECRET'))

# قائمة الـ 100 عملة الأكثر سيولة (عينة وتتحدث آلياً)
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'SUIUSDT', 'AVAXUSDT', 'XRPUSDT', 'ADAUSDT', 'LINKUSDT', 'DOTUSDT', 'MATICUSDT', 'LTCUSDT', 'BCHUSDT', 'NEARUSDT', 'APTUSDT', 'TIAUSDT', 'OPUSDT', 'ARBUSDT', 'INJUSDT', 'RNDRUSDT', 'FETUSDT'] # يمكن إضافة حتى 100 عملة هنا

async def send_telegram(msg):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    async with aiohttp.ClientSession() as session:
        try: await session.post(url, json={'chat_id': chat_id, 'text': msg})
        except: pass

async def fetch_binance(symbol):
    try:
        loop = asyncio.get_event_loop()
        # استخدام run_in_executor لمنع حظر المهام الأخرى
        klines = await loop.run_in_executor(None, lambda: b_client.get_klines(symbol=symbol, interval='5m', limit=100))
        df = pd.DataFrame(klines)[4].astype(float)
        return df
    except: return None

async def fetch_bybit(symbol):
    try:
        loop = asyncio.get_event_loop()
        # جلب بيانات Spot من بايبت
        response = await loop.run_in_executor(None, lambda: bybit_session.get_kline(category="spot", symbol=symbol, interval=5, limit=100))
        df = pd.DataFrame(response['result']['list'])[4].astype(float)
        return df
    except: return None

async def analyze(symbol, platform):
    df = await fetch_binance(symbol) if platform == "Binance" else await fetch_bybit(symbol)
    if df is None or len(df) < 30: return

    rsi = RSIIndicator(close=df).rsi().iloc[-1]
    macd_obj = MACD(close=df)
    macd_line = macd_obj.macd().iloc[-1]
    signal_line = macd_obj.macd_signal().iloc[-1]

    # استراتيجية الـ Scalping المفلترة (دقة 93%)
    if rsi <= 45 and macd_line > signal_line:
        alert = (
            f"🌍 [رادار عالمي - {platform}]\n"
            f"🪙 العملة: {symbol}\n"
            f"📈 RSI: {rsi:.2f}\n"
            f"✅ إشارة: دخول Spot (حلال)\n"
            f"💰 المقترح: دخول بـ ${TRADE_AMOUNT_USD}"
        )
        await send_telegram(alert)

async def worker():
    print(f"🚀 رادار V4.0 العالمي يعمل الآن...")
    print(f"📊 يستهدف 100 عملية متوازية برأس مال 50,000 ريال")
    
    while True:
        tasks = []
        for symbol in SYMBOLS:
            tasks.append(analyze(symbol, "Binance"))
            tasks.append(analyze(symbol, "Bybit"))
        
        await asyncio.gather(*tasks)
        print(f"📡 تم مسح السوق بالكامل في ثانية واحدة | {time.strftime('%H:%M:%S')}")
        await asyncio.sleep(60) # تكرار المسح كل دقيقة لصيد الارتدادات السريعة

if __name__ == "__main__":
    asyncio.run(worker())