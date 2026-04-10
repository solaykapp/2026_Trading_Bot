import os
import json
import time
import logging
import asyncio
import aiohttp
import pandas as pd
import pandas_ta as ta
import git  # تم الإضافة للربط مع GitHub
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(override=True)

# ══════════════════════════════════════════════════════════════
# ─── الإعدادات (Settings)
# ══════════════════════════════════════════════════════════════
INITIAL_BALANCE   = float(os.getenv("INITIAL_BALANCE", 10_000))
TRADE_RISK_PCT    = float(os.getenv("TRADE_RISK_PCT",  0.02))
MAX_OPEN_TRADES   = int(os.getenv("MAX_OPEN_TRADES",    5))
SCAN_INTERVAL_SEC = int(os.getenv("SCAN_INTERVAL_SEC",  60))
MIN_SCORE         = int(os.getenv("MIN_SCORE",          3))
TRAILING_PCT      = float(os.getenv("TRAILING_PCT",     0.008))
SYMBOLS_FILE      = os.getenv("SYMBOLS_FILE", "halal_crypto_100_list_2026.txt")

# التوكنات السرية
TELEGRAM_TOKEN    = os.getenv("TELEGRAM_TOKEN",    "")
TELEGRAM_CHAT_ID  = os.getenv("TELEGRAM_CHAT_ID", "")
GITHUB_TOKEN      = os.getenv("GITHUB_TOKEN",      "") # ضروري لرفع البيانات لـ Lovable

BINANCE_BASE      = "https://api.binance.com/api/v3"

# ══════════════════════════════════════════════════════════════
# ─── Logging & Status
# ══════════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("simulator.log", encoding="utf-8")]
)
log = logging.getLogger("TradingBot")

state = {
    "balance": INITIAL_BALANCE,
    "initial_balance": INITIAL_BALANCE,
    "open_trades": {},
    "closed_trades": [],
    "total_pnl": 0.0,
    "win_count": 0,
    "loss_count": 0,
    "cycle": 0,
    "valid_symbols": [],
    "skipped_symbols": [],
}

# ══════════════════════════════════════════════════════════════
# ─── وظيفة الرفع لـ GitHub (الجسر البرمجي لـ Lovable)
# ══════════════════════════════════════════════════════════════
def push_to_github():
    """ترفع ملف الإحصائيات لـ GitHub لكي يظهر حياً في Lovable"""
    try:
        if not GITHUB_TOKEN:
            log.warning("⚠️ GITHUB_TOKEN غير موجود. التحديث في Lovable معطل.")
            return

        repo_url = f"https://{GITHUB_TOKEN}@github.com/solaykapp/2026_Trading_Bot.git"
        repo = git.Repo(".")
        
        # إعداد هوية البوت للـ Commit
        with repo.config_writer() as cw:
            cw.set_value("user", "name", "TradingBot_V2_Live")
            cw.set_value("user", "email", "bot@trading.com")
            
        if repo.is_dirty(untracked_files=True):
            repo.git.add("dashboard_stats.json")
            repo.index.commit(f"🤖 Market Update: {datetime.now().strftime('%H:%M:%S')}")
            origin = repo.remotes.origin
            origin.set_url(repo_url)
            origin.push()
            log.info("✅ تم رفع التحديث لـ GitHub بنجاح.")
    except Exception as e:
        log.error(f"❌ خطأ في مزامنة Git: {e}")

# ══════════════════════════════════════════════════════════════
# ─── العملات والبيانات (Binance)
# ══════════════════════════════════════════════════════════════
def load_symbols(filepath: str) -> list[str]:
    path = Path(filepath)
    if not path.exists(): return []
    symbols = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            sym = line.strip().upper()
            if not sym or sym.startswith("#"): continue
            if not sym.endswith("USDT"): sym += "USDT"
            symbols.append(sym)
    return symbols

async def validate_symbols(session: aiohttp.ClientSession, symbols: list[str]):
    url = f"{BINANCE_BASE}/exchangeInfo"
    async with session.get(url) as r:
        if r.status == 200:
            data = await r.json()
            available = {s["symbol"] for s in data["symbols"] if s["status"] == "TRADING"}
            valid = [s for s in symbols if s in available]
            skipped = [s for s in symbols if s not in available]
            return valid, skipped
    return symbols, []

async def fetch_klines(session, symbol, interval="5m", limit=150):
    url = f"{BINANCE_BASE}/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    try:
        async with session.get(url, params=params) as r:
            if r.status == 200:
                data = await r.json()
                df = pd.DataFrame(data, columns=["open_time","open","high","low","close","volume","ct","qv","t","tb","tq","i"])
                for col in ["open","high","low","close","volume"]: df[col] = df[col].astype(float)
                return df
    except: return None

async def fetch_price(session, symbol):
    url = f"{BINANCE_BASE}/ticker/price"
    try:
        async with session.get(url, params={"symbol": symbol}) as r:
            if r.status == 200: return float((await r.json())["price"])
    except: pass
    return 0.0

# ══════════════════════════════════════════════════════════════
# ─── التحليل الفني ونظام النقاط
# ══════════════════════════════════════════════════════════════
def compute_indicators(df):
    if df is None or len(df) < 60: return None
    close, high, low, volume = df["close"], df["high"], df["low"], df["volume"]
    rsi = ta.rsi(close, length=14)
    macd = ta.macd(close)
    ema20 = ta.ema(close, length=20)
    ema50 = ta.ema(close, length=50)
    atr = ta.atr(high, low, close, length=14)
    bb = ta.bbands(close, length=20)
    vol_avg = volume.rolling(20).mean()

    return {
        "price": round(close.iloc[-1], 6),
        "rsi": round(rsi.iloc[-1], 2),
        "macd_hist": round(macd["MACDh_12_26_9"].iloc[-1], 4),
        "macd_hist_prev": round(macd["MACDh_12_26_9"].iloc[-2], 4),
        "ema20": ema20.iloc[-1], "ema50": ema50.iloc[-1],
        "atr": atr.iloc[-1], "bb_lower": bb["BBL_20_2.0"].iloc[-1],
        "vol_ratio": round(volume.iloc[-1] / vol_avg.iloc[-1], 2)
    }

def score_signal(ind_5m, ind_1h):
    if not ind_5m: return 0, None, []
    score = 0
    reasons = []
    
    # Scalp Logic
    if ind_5m["rsi"] < 38: score += 1; reasons.append("RSI Oversold")
    if ind_5m["macd_hist"] > 0 and ind_5m["macd_hist_prev"] <= 0: score += 2; reasons.append("MACD Cross Up")
    if ind_5m["vol_ratio"] >= 1.8: score += 1; reasons.append("Volume Spike")
    
    # Trend Confirm
    if ind_1h and ind_1h["ema20"] > ind_1h["ema50"]: score += 1; reasons.append("1H Trend Up")

    if score >= MIN_SCORE: return score, "scalp_long", reasons
    return score, None, []

# ══════════════════════════════════════════════════════════════
# ─── إدارة الصفقات والحفظ
# ══════════════════════════════════════════════════════════════
def open_trade(symbol, signal, score, ind, reasons):
    if len(state["open_trades"]) >= MAX_OPEN_TRADES: return False
    price, atr = ind["price"], ind["atr"] or price * 0.005
    sl = round(price - atr * 1.5, 6)
    tp = round(price + atr * 2.5, 6)
    
    risk_amount = state["balance"] * TRADE_RISK_PCT
    qty = round(risk_amount / (price - sl), 6) if price > sl else 0
    
    if qty > 0:
        state["open_trades"][symbol] = {
            "symbol": symbol, "mode": "Scalp", "entry": price, "sl": sl, "tp": tp,
            "trailing_sl": sl, "highest_price": price, "qty": qty, "score": score,
            "open_time": datetime.now().strftime("%H:%M:%S"), "reasons": reasons
        }
        log.info(f"✅ تم فتح صفقة: {symbol} بسعر {price}")
        return True
    return False

def update_open_trades(prices):
    to_close = []
    for sym, trade in state["open_trades"].items():
        price = prices.get(sym, 0)
        if price <= 0: continue
        
        # Trailing Stop Logic
        if price > trade["highest_price"]:
            trade["highest_price"] = price
            new_tsl = round(price * (1 - TRAILING_PCT), 6)
            if new_tsl > trade["trailing_sl"]: trade["trailing_sl"] = new_tsl
            
        pnl = (price - trade["entry"]) * trade["qty"]
        if price <= max(trade["sl"], trade["trailing_sl"]) or price >= trade["tp"]:
            to_close.append((sym, price, pnl))
            
    for sym, exit_p, pnl in to_close:
        t = state["open_trades"].pop(sym)
        state["balance"] += pnl
        state["total_pnl"] += pnl
        if pnl > 0: state["win_count"] += 1
        else: state["loss_count"] += 1
        state["closed_trades"].append({**t, "exit": exit_p, "pnl": round(pnl, 2)})

def save_dashboard():
    total = state["win_count"] + state["loss_count"]
    dashboard = {
        "balance": round(state["balance"], 2),
        "total_pnl": round(state["total_pnl"], 2),
        "roi_pct": round((state["total_pnl"] / state["initial_balance"]) * 100, 2),
        "open_trades_count": len(state["open_trades"]),
        "win_rate_pct": round(state["win_count"] / total * 100, 1) if total > 0 else 0,
        "open_trades": list(state["open_trades"].values()),
        "last_closed": state["closed_trades"][-10:],
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "market_status": "🟢 Running Live"
    }
    with open("dashboard_stats.json", "w", encoding="utf-8") as f:
        json.dump(dashboard, f, indent=4)

# ══════════════════════════════════════════════════════════════
# ─── المحرك الرئيسي
# ══════════════════════════════════════════════════════════════
async def run_simulator():
    all_symbols = load_symbols(SYMBOLS_FILE)
    async with aiohttp.ClientSession() as session:
        valid, skipped = await validate_symbols(session, all_symbols)
        state["valid_symbols"] = valid
        
        while True:
            state["cycle"] += 1
            log.info(f"🔄 الدورة #{state['cycle']}")
            
            if state["open_trades"]:
                prices = {s: await fetch_price(session, s) for s in state["open_trades"]}
                update_open_trades(prices)
            
            for symbol in state["valid_symbols"]:
                if symbol in state["open_trades"] or len(state["open_trades"]) >= MAX_OPEN_TRADES: continue
                df5, df1 = await asyncio.gather(fetch_klines(session, symbol, "5m"), fetch_klines(session, symbol, "1h"))
                ind5, ind1 = compute_indicators(df5), compute_indicators(df1)
                score, signal, reasons = score_signal(ind5, ind1)
                if signal: open_trade(symbol, signal, score, ind5, reasons)
                await asyncio.sleep(0.1)
                
            save_dashboard()
            push_to_github() # رفع البيانات لـ Lovable
            await asyncio.sleep(SCAN_INTERVAL_SEC)

if __name__ == "__main__":
    asyncio.run(run_simulator())