"""
🤖 Trading Simulator V1
محاكي تداول حقيقي بدون مال حقيقي
- بيانات حقيقية من Binance (بدون API Key)
- RSI + MACD + Volume
- Scalping + Swing Trading
- Stop-Loss / Take-Profit حقيقي
- سجل كامل للصفقات
"""
 
import os
import json
import time
import asyncio
import aiohttp
import pandas as pd
import pandas_ta as ta
from datetime import datetime
from dotenv import load_dotenv
 
load_dotenv(override=True)
 
# ─── إعدادات المحاكاة ─────────────────────────────────────────────────────────
INITIAL_BALANCE     = float(os.getenv("INITIAL_BALANCE", 10_000))   # USDT افتراضي
TRADE_RISK_PCT      = float(os.getenv("TRADE_RISK_PCT",  0.02))     # 2% من الرصيد لكل صفقة
TELEGRAM_TOKEN      = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID    = os.getenv("TELEGRAM_CHAT_ID", "")
 
# العملات الحلال المراد مراقبتها (يمكن التوسيع)
HALAL_SYMBOLS = [
    "BTCUSDT","ETHUSDT","BNBUSDT","ADAUSDT","XRPUSDT",
    "DOTUSDT","LINKUSDT","LTCUSDT","XLMUSDT","ALGOUSDT",
    "MATICUSDT","SOLUSDT","AVAXUSDT","ATOMUSDT","NEARUSDT",
    "FTMUSDT","SANDUSDT","MANAUSDT","AAVEUSDT","UNIUSDT",
]
 
BINANCE_BASE = "https://api.binance.com/api/v3"
 
# ─── حالة المحاكاة ────────────────────────────────────────────────────────────
state = {
    "balance":        INITIAL_BALANCE,
    "initial_balance": INITIAL_BALANCE,
    "open_trades":    {},   # symbol -> trade_dict
    "closed_trades":  [],
    "total_pnl":      0.0,
    "win_count":      0,
    "loss_count":     0,
    "cycle":          0,
}
 
# ─── Binance: جلب بيانات حقيقية ───────────────────────────────────────────────
async def fetch_klines(session: aiohttp.ClientSession, symbol: str, interval="5m", limit=100):
    url = f"{BINANCE_BASE}/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    try:
        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as r:
            if r.status == 200:
                data = await r.json()
                df = pd.DataFrame(data, columns=[
                    "open_time","open","high","low","close","volume",
                    "close_time","quote_vol","trades","taker_base","taker_quote","ignore"
                ])
                for col in ["open","high","low","close","volume"]:
                    df[col] = df[col].astype(float)
                return df
    except Exception as e:
        print(f"  ⚠️ {symbol}: {e}")
    return None
 
async def fetch_price(session: aiohttp.ClientSession, symbol: str) -> float:
    url = f"{BINANCE_BASE}/ticker/price"
    try:
        async with session.get(url, params={"symbol": symbol}, timeout=aiohttp.ClientTimeout(total=5)) as r:
            if r.status == 200:
                d = await r.json()
                return float(d["price"])
    except:
        pass
    return 0.0
 
# ─── حساب المؤشرات ────────────────────────────────────────────────────────────
def compute_indicators(df: pd.DataFrame) -> dict:
    close = df["close"]
    volume = df["volume"]
 
    rsi   = ta.rsi(close, length=14)
    macd  = ta.macd(close, fast=12, slow=26, signal=9)
    ema20 = ta.ema(close, length=20)
    ema50 = ta.ema(close, length=50)
    atr   = ta.atr(df["high"], df["low"], close, length=14)
 
    vol_avg = volume.rolling(20).mean()
 
    return {
        "rsi":       round(float(rsi.iloc[-1]),    2) if rsi   is not None else 50,
        "macd":      round(float(macd["MACD_12_26_9"].iloc[-1]),   4) if macd is not None else 0,
        "signal":    round(float(macd["MACDs_12_26_9"].iloc[-1]),  4) if macd is not None else 0,
        "macd_hist": round(float(macd["MACDh_12_26_9"].iloc[-1]),  4) if macd is not None else 0,
        "ema20":     round(float(ema20.iloc[-1]),  4) if ema20 is not None else 0,
        "ema50":     round(float(ema50.iloc[-1]),  4) if ema50 is not None else 0,
        "atr":       round(float(atr.iloc[-1]),    6) if atr   is not None else 0,
        "vol_ratio": round(float(volume.iloc[-1] / vol_avg.iloc[-1]), 2) if vol_avg.iloc[-1] > 0 else 1,
        "price":     round(float(close.iloc[-1]),  6),
    }
 
# ─── استراتيجية الدخول ────────────────────────────────────────────────────────
def check_entry_signal(ind: dict, mode="both") -> str | None:
    """
    يرجع: 'scalp_long' | 'swing_long' | None
    """
    rsi, macd_h, vol, ema20, ema50, price = (
        ind["rsi"], ind["macd_hist"], ind["vol_ratio"],
        ind["ema20"], ind["ema50"], ind["price"]
    )
 
    # Scalping: RSI oversold + MACD cross + حجم مرتفع
    scalp = (
        rsi < 35 and
        macd_h > 0 and
        vol >= 1.5 and
        price > ema20 * 0.995
    )
 
    # Swing: EMA20 > EMA50 + RSI بين 40-60 + MACD إيجابي
    swing = (
        ema20 > ema50 and
        40 < rsi < 60 and
        macd_h > 0 and
        vol >= 1.2
    )
 
    if mode in ("scalp", "both") and scalp:
        return "scalp_long"
    if mode in ("swing", "both") and swing:
        return "swing_long"
    return None
 
# ─── فتح صفقة محاكاة ─────────────────────────────────────────────────────────
def open_trade(symbol: str, signal: str, ind: dict):
    price = ind["price"]
    atr   = ind["atr"] if ind["atr"] > 0 else price * 0.005
 
    # SL/TP بناءً على ATR
    if signal == "scalp_long":
        sl = round(price - atr * 1.5, 6)
        tp = round(price + atr * 2.0, 6)
        mode = "Scalping"
    else:
        sl = round(price - atr * 2.5, 6)
        tp = round(price + atr * 4.0, 6)
        mode = "Swing"
 
    risk_amount = state["balance"] * TRADE_RISK_PCT
    qty         = round(risk_amount / (price - sl), 6) if price > sl else 0
    if qty <= 0:
        return
 
    trade = {
        "symbol":     symbol,
        "mode":       mode,
        "entry":      price,
        "sl":         sl,
        "tp":         tp,
        "qty":        qty,
        "cost":       round(qty * price, 2),
        "open_time":  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "rsi_entry":  ind["rsi"],
    }
 
    state["open_trades"][symbol] = trade
    print(f"\n  ✅ [{mode}] فتح صفقة {symbol} @ {price} | SL={sl} | TP={tp} | qty={qty}")
 
# ─── تحديث الصفقات المفتوحة ───────────────────────────────────────────────────
def update_open_trades(prices: dict):
    to_close = []
    for sym, trade in state["open_trades"].items():
        price = prices.get(sym, 0)
        if price <= 0:
            continue
 
        pnl = (price - trade["entry"]) * trade["qty"]
 
        if price <= trade["sl"]:
            to_close.append((sym, price, pnl, "❌ Stop-Loss"))
        elif price >= trade["tp"]:
            to_close.append((sym, price, pnl, "✅ Take-Profit"))
 
    for sym, exit_price, pnl, reason in to_close:
        trade = state["open_trades"].pop(sym)
        trade["exit"]       = exit_price
        trade["pnl"]        = round(pnl, 4)
        trade["close_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        trade["reason"]     = reason
 
        state["balance"]      += pnl
        state["total_pnl"]    += pnl
        state["closed_trades"].append(trade)
 
        if pnl >= 0:
            state["win_count"] += 1
        else:
            state["loss_count"] += 1
 
        print(f"  {reason} | {sym} PnL={pnl:+.2f} USDT | رصيد={state['balance']:.2f}")
 
# ─── حفظ الحالة في JSON ───────────────────────────────────────────────────────
def save_dashboard():
    total_trades = state["win_count"] + state["loss_count"]
    win_rate     = round(state["win_count"] / total_trades * 100, 1) if total_trades > 0 else 0
 
    dashboard = {
        "balance":           round(state["balance"], 2),
        "initial_balance":   state["initial_balance"],
        "total_pnl":         round(state["total_pnl"], 2),
        "pnl_pct":           round(state["total_pnl"] / state["initial_balance"] * 100, 2),
        "open_trades_count": len(state["open_trades"]),
        "total_closed":      total_trades,
        "win_count":         state["win_count"],
        "loss_count":        state["loss_count"],
        "win_rate_pct":      win_rate,
        "open_trades":       list(state["open_trades"].values()),
        "last_closed":       state["closed_trades"][-10:],
        "market_status":     "Simulator Running 🟢",
        "last_updated":      datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cycle":             state["cycle"],
    }
 
    with open("dashboard_stats.json", "w", encoding="utf-8") as f:
        json.dump(dashboard, f, indent=4, ensure_ascii=False)
 
# ─── إرسال تليجرام ────────────────────────────────────────────────────────────
async def send_telegram(session: aiohttp.ClientSession, message: str):
    if not TELEGRAM_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        await session.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        })
    except:
        pass
 
# ─── المحرك الرئيسي ───────────────────────────────────────────────────────────
async def run_simulator():
    print("=" * 60)
    print("🚀 Trading Simulator V1 — بيانات حقيقية، أموال وهمية")
    print(f"   رأس المال: {INITIAL_BALANCE:,.0f} USDT")
    print(f"   عدد العملات: {len(HALAL_SYMBOLS)}")
    print("=" * 60)
 
    async with aiohttp.ClientSession() as session:
        while True:
            state["cycle"] += 1
            print(f"\n🔄 دورة #{state['cycle']} — {datetime.now().strftime('%H:%M:%S')}")
 
            # 1. تحديث أسعار الصفقات المفتوحة أولاً
            if state["open_trades"]:
                live_prices = {}
                for sym in list(state["open_trades"].keys()):
                    live_prices[sym] = await fetch_price(session, sym)
                update_open_trades(live_prices)
 
            # 2. مسح العملات عن إشارات جديدة
            signals_found = 0
            for symbol in HALAL_SYMBOLS:
                # لا نفتح صفقة إذا كانت مفتوحة مسبقاً
                if symbol in state["open_trades"]:
                    continue
 
                df = await fetch_klines(session, symbol, interval="5m")
                if df is None or len(df) < 60:
                    continue
 
                ind    = compute_indicators(df)
                signal = check_entry_signal(ind, mode="both")
 
                if signal:
                    signals_found += 1
                    open_trade(symbol, signal, ind)
 
                    msg = (
                        f"📡 *إشارة محاكاة — {symbol}*\n"
                        f"النوع: `{signal}`\n"
                        f"السعر: `{ind['price']}`\n"
                        f"RSI: `{ind['rsi']}`\n"
                        f"MACD Hist: `{ind['macd_hist']}`\n"
                        f"حجم × المتوسط: `{ind['vol_ratio']}`\n"
                        f"🔵 هذه محاكاة فقط — لا أموال حقيقية"
                    )
                    await send_telegram(session, msg)
 
                await asyncio.sleep(0.2)  # تجنب Rate Limit
 
            print(f"  📊 إشارات جديدة: {signals_found} | مفتوحة: {len(state['open_trades'])} | رصيد: {state['balance']:.2f} USDT")
 
            # 3. حفظ الحالة
            save_dashboard()
 
            # انتظار 60 ثانية قبل الدورة القادمة
            await asyncio.sleep(60)
 
if __name__ == "__main__":
    asyncio.run(run_simulator())