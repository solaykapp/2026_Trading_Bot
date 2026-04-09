import requests
import pandas as pd
import time
import schedule
import logging
import os
import re
import subprocess
from datetime import datetime
from binance.client import Client
from openai import OpenAI

# ─────────────────────────────────────────────
#    ⚙️  إعدادات 2026_Trading_Simulator (الإصدار الأوتوماتيكي)
# ─────────────────────────────────────────────
CONFIG = {
    "TELEGRAM_TOKEN": "8623422400:AAHZ6FSMWANcbk3bg0IKAbR1Te3LTqViYy0",
    "TELEGRAM_CHAT_ID": "1633067596",
    "PPLX_API_KEY": "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",
    "BINANCE_API_KEY": "8t26FeqsNQdtLa7ckVTuvNsFbZFhyJkqLgCzChJTpYgrdBQvvh17XonimZCXd1CK",
    "BINANCE_SECRET_KEY": "اكتب_هنا_السيكرت_كي_الخاص_بك", 
    "CSV_FILE": "trading_data.csv",
    "HALAL_FILE": "halal_crypto_100_list_2026.txt",
    "STABLE_COINS": ["USDC", "USDT", "FDUSD", "TUSD", "DAI", "PYUSD", "USDP"]
}

# تهيئة الاتصالات
binance_client = Client(CONFIG["BINANCE_API_KEY"], CONFIG["BINANCE_SECRET_KEY"])
pplx_client = OpenAI(api_key=CONFIG["PPLX_API_KEY"], base_url="https://api.perplexity.ai")
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s", datefmt="%H:%M:%S")

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / (loss + 1e-9)
    return 100 - (100 / (1 + rs))

def get_symbols():
    if not os.path.exists(CONFIG["HALAL_FILE"]): return []
    symbols = []
    try:
        with open(CONFIG["HALAL_FILE"], "r") as f:
            for line in f:
                match = re.search(r'([A-Z0-9]+)', line.upper())
                if match:
                    symbol = match.group(1)
                    if 2 <= len(symbol) <= 6 and symbol not in CONFIG["STABLE_COINS"]:
                        symbols.append(f"{symbol}USDT")
        return list(set(symbols))
    except: return []

def check_binance_confirmation(symbol):
    try:
        klines = binance_client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_5MINUTE, limit=10)
        current_vol = float(klines[-1][5])
        avg_vol = sum(float(k[5]) for k in klines[:-1]) / 9
        return current_vol > (avg_vol * 1.05)
    except: return False

def get_ai_sentiment(symbol):
    coin = symbol.replace("USDT", "")
    try:
        prompt = f"Check {coin} crypto news last 2h. Any negative risks? Reply: SAFE or RISKY + 5 words."
        response = pplx_client.chat.completions.create(model="sonar", messages=[{"role": "user", "content": prompt}], timeout=10)
        return response.choices[0].message.content
    except: return "NEUTRAL"

def auto_push_to_github(found_count):
    """رفع التعديلات تلقائياً إلى GitHub دون تدخل بشري"""
    try:
        logging.info("📤 جاري مزامنة البيانات الجديدة مع GitHub...")
        subprocess.run(["git", "add", "."], check=True)
        commit_msg = f"Auto-Update: Captured {found_count} opportunities at {datetime.now().strftime('%H:%M')}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        subprocess.run(["git", "push"], check=True)
        logging.info("✅ تم الرفع والمزامنة بنجاح!")
    except Exception as e:
        logging.error(f"⚠️ فشل الرفع التلقائي: {e}")

def save_to_cumulative_csv(new_hits):
    if not new_hits: return
    
    new_df = pd.DataFrame(new_hits)
    
    if os.path.exists(CONFIG["CSV_FILE"]):
        old_df = pd.read_csv(CONFIG["CSV_FILE"])
        combined_df = pd.concat([old_df, new_df]).drop_duplicates(subset=['Symbol'], keep='last')
        combined_df.to_csv(CONFIG["CSV_FILE"], index=False)
    else:
        new_df.to_csv(CONFIG["CSV_FILE"], index=False)
    
    # استدعاء الأتمتة فور الحفظ
    auto_push_to_github(len(new_hits))

def run_trading_cycle():
    symbols = get_symbols()
    logging.info(f"🧐 دورة فحص ذكية لـ {len(symbols)} عملة...")
    current_cycle_hits = []

    for symbol in symbols:
        try:
            url = "https://api.bybit.com/v5/market/kline"
            res = requests.get(url, params={"category": "spot", "symbol": symbol, "interval": "5", "limit": 30}).json()
            
            if res["retCode"] == 0:
                df = pd.DataFrame(res["result"]["list"], columns=["ts", "o", "h", "l", "c", "v", "t"])
                df[["o", "c"]] = df[["o", "c"]].apply(pd.to_numeric)
                df = df.iloc[::-1]
                
                price = df["c"].iloc[-1]
                rsi = calculate_rsi(df["c"]).iloc[-1]
                
                if 40 <= rsi <= 65 and price > df["o"].iloc[-1]:
                    if check_binance_confirmation(symbol):
                        ai_res = get_ai_sentiment(symbol)
                        if "SAFE" in ai_res.upper():
                            hit = {
                                "Time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "Symbol": symbol,
                                "Price": price,
                                "RSI": round(rsi, 1),
                                "AI_Opinion": ai_res
                            }
                            current_cycle_hits.append(hit)
                            
                            msg = f"🚀 *قنص أوتوماتيكي*\n🪙 {symbol}\n💰 السعر: `{price}`\n🛡️ AI: `{ai_res}`"
                            requests.post(f"https://api.telegram.org/bot{CONFIG['TELEGRAM_TOKEN']}/sendMessage", 
                                          json={"chat_id": CONFIG["TELEGRAM_CHAT_ID"], "text": msg, "parse_mode": "Markdown"})
            time.sleep(0.01)
        except: continue

    save_to_cumulative_csv(current_cycle_hits)

if __name__ == "__main__":
    run_trading_cycle()
    schedule.every(5).minutes.do(run_trading_cycle)
    while True:
        schedule.run_pending()
        time.sleep(1)