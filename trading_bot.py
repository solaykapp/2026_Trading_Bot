"""
╔══════════════════════════════════════════════════════════════════╗
║     🤖 OSAMA TRADING BOT - v3.0                                  ║
║     تحليل RSI + MACD + إشعارات بيع/شراء واضحة على تليجرام      ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import time
import logging
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv(override=True)

# ══════════════════════════════════════════════════════════════
# الإعدادات
# ══════════════════════════════════════════════════════════════
TELEGRAM_TOKEN   = os.getenv('TELEGRAM_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
BINANCE_BASE     = 'https://api.binance.com/api/v3'

SYMBOLS = [
    'BTCUSDT', 'ETHUSDT', 'SUIUSDT',
    'SOLUSDT', 'AVAXUSDT', 'BNBUSDT'
]

RSI_BUY_LEVEL  = 35   # RSI أقل من هذا = فرصة شراء
RSI_SELL_LEVEL = 65   # RSI أكبر من هذا = فرصة بيع
SCAN_INTERVAL  = 180  # كل 3 دقائق

# تتبع الإشعارات لتجنب التكرار
last_signals: dict = {}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger('TradingBot')


# ══════════════════════════════════════════════════════════════
# جلب البيانات
# ══════════════════════════════════════════════════════════════
def get_klines(symbol: str, interval: str = '15m', limit: int = 100) -> pd.DataFrame:
    """جلب بيانات الشموع من Binance."""
    try:
        r = requests.get(f'{BINANCE_BASE}/klines',
            params={'symbol': symbol, 'interval': interval, 'limit': limit},
            timeout=10)
        if r.status_code == 200:
            df = pd.DataFrame(r.json())
            df['close'] = df[4].astype(float)
            df['high']  = df[2].astype(float)
            df['low']   = df[3].astype(float)
            df['vol']   = df[5].astype(float)
            return df
    except Exception as e:
        log.error(f'klines error {symbol}: {e}')
    return pd.DataFrame()


def get_current_price(symbol: str) -> float:
    """جلب السعر الحالي."""
    try:
        r = requests.get(f'{BINANCE_BASE}/ticker/price',
            params={'symbol': symbol}, timeout=10)
        if r.status_code == 200:
            return float(r.json()['price'])
    except:
        pass
    return 0.0


# ══════════════════════════════════════════════════════════════
# المؤشرات الفنية (بدون مكتبات خارجية)
# ══════════════════════════════════════════════════════════════
def calc_rsi(closes: pd.Series, period: int = 14) -> float:
    """حساب مؤشر RSI."""
    delta = closes.diff()
    gain  = delta.clip(lower=0).rolling(period).mean()
    loss  = (-delta.clip(upper=0)).rolling(period).mean()
    rs    = gain / loss.replace(0, 1e-10)
    rsi   = 100 - (100 / (1 + rs))
    return round(rsi.iloc[-1], 2)


def calc_macd(closes: pd.Series):
    """حساب MACD والإشارة."""
    ema12    = closes.ewm(span=12).mean()
    ema26    = closes.ewm(span=26).mean()
    macd     = ema12 - ema26
    signal   = macd.ewm(span=9).mean()
    hist     = macd - signal
    return round(hist.iloc[-1], 6), round(hist.iloc[-2], 6)


def calc_ema(closes: pd.Series, period: int) -> float:
    """حساب المتوسط المتحرك الأسي."""
    return round(closes.ewm(span=period).mean().iloc[-1], 6)


# ══════════════════════════════════════════════════════════════
# تحليل الإشارة
# ══════════════════════════════════════════════════════════════
def analyze_symbol(symbol: str) -> dict:
    """
    تحليل العملة وتحديد إشارة BUY أو SELL أو HOLD.
    يعيد dict بجميع التفاصيل.
    """
    df = get_klines(symbol, '15m', 100)
    if df.empty or len(df) < 30:
        return {'signal': 'ERROR', 'symbol': symbol}

    closes = df['close']
    price  = get_current_price(symbol)
    rsi    = calc_rsi(closes)
    macd_hist, macd_prev = calc_macd(closes)
    ema20  = calc_ema(closes, 20)
    ema50  = calc_ema(closes, 50)

    # ─── شروط الشراء ───
    buy_conditions = [
        rsi <= RSI_BUY_LEVEL,                          # RSI منخفض
        macd_hist > 0 and macd_prev <= 0,              # تقاطع MACD صاعد
        price > ema20,                                  # السعر فوق EMA20
    ]

    # ─── شروط البيع ───
    sell_conditions = [
        rsi >= RSI_SELL_LEVEL,                         # RSI مرتفع
        macd_hist < 0 and macd_prev >= 0,              # تقاطع MACD هابط
        price < ema20,                                  # السعر تحت EMA20
    ]

    buy_score  = sum(buy_conditions)
    sell_score = sum(sell_conditions)

    if buy_score >= 2:
        signal = 'BUY'
    elif sell_score >= 2:
        signal = 'SELL'
    else:
        signal = 'HOLD'

    return {
        'symbol':     symbol,
        'signal':     signal,
        'price':      price,
        'rsi':        rsi,
        'macd_hist':  macd_hist,
        'ema20':      ema20,
        'ema50':      ema50,
        'buy_score':  buy_score,
        'sell_score': sell_score,
    }


# ══════════════════════════════════════════════════════════════
# إشعارات تليجرام
# ══════════════════════════════════════════════════════════════
def send_signal(data: dict):
    """إرسال إشعار بيع أو شراء واضح عبر تليجرام."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return

    signal = data['signal']
    symbol = data['symbol'].replace('USDT', '')

    if signal == 'BUY':
        icon    = '🟢'
        action  = 'فرصة شراء'
        emoji   = '📈'
    else:
        icon    = '🔴'
        action  = 'فرصة بيع'
        emoji   = '📉'

    # حساب مستويات TP و SL تقريبية
    price = data['price']
    if signal == 'BUY':
        tp = round(price * 1.02, 4)   # هدف +2%
        sl = round(price * 0.99, 4)   # وقف -1%
    else:
        tp = round(price * 0.98, 4)   # هدف -2%
        sl = round(price * 1.01, 4)   # وقف +1%

    message = (
        f"{icon} *{action} | {symbol}* {emoji}\n"
        f"{'━' * 28}\n"
        f"💰 السعر: `${price:,.4f}`\n\n"
        f"📊 *المؤشرات*\n"
        f"RSI: `{data['rsi']}`  {'🔥 ذروة بيع' if data['rsi'] <= RSI_BUY_LEVEL else '⚡ ذروة شراء' if data['rsi'] >= RSI_SELL_LEVEL else ''}\n"
        f"MACD: `{data['macd_hist']:+.6f}`\n"
        f"EMA20: `${data['ema20']:,.4f}`\n\n"
        f"🎯 *مستويات التداول*\n"
        f"الدخول: `${price:,.4f}`\n"
        f"الهدف TP: `${tp:,.4f}` (+2%)\n"
        f"الوقف SL: `${sl:,.4f}` (-1%)\n\n"
        f"{'━' * 28}\n"
        f"⚠️ _هذا تحليل آلي — ليس نصيحة مالية_"
    )

    try:
        requests.post(
            f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage',
            json={
                'chat_id':    TELEGRAM_CHAT_ID,
                'text':       message,
                'parse_mode': 'Markdown'
            },
            timeout=10
        )
        log.info(f'تليجرام: {signal} {symbol}')
    except Exception as e:
        log.error(f'تليجرام فشل: {e}')


def should_send_signal(symbol: str, signal: str) -> bool:
    """
    منع إرسال نفس الإشارة للعملة مرتين متتاليتين.
    يرسل فقط إذا تغيرت الإشارة.
    """
    last = last_signals.get(symbol)
    if last == signal:
        return False
    last_signals[symbol] = signal
    return True


# ══════════════════════════════════════════════════════════════
# الحلقة الرئيسية
# ══════════════════════════════════════════════════════════════
def run_bot():
    """الحلقة الرئيسية — تفحص العملات كل 3 دقائق."""
    log.info('=' * 55)
    log.info('   🚀 OSAMA TRADING BOT v3.0 — انطلق!')
    log.info(f'   العملات: {", ".join(s.replace("USDT","") for s in SYMBOLS)}')
    log.info(f'   RSI شراء: ≤{RSI_BUY_LEVEL} | RSI بيع: ≥{RSI_SELL_LEVEL}')
    log.info('=' * 55)

    # إشعار بدء التشغيل
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        requests.post(
            f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage',
            json={
                'chat_id':    TELEGRAM_CHAT_ID,
                'text':       '🤖 *OSAMA TRADING BOT v3.0 انطلق!*\nجاري مراقبة السوق...',
                'parse_mode': 'Markdown'
            },
            timeout=10
        )

    while True:
        log.info(f'🔍 فحص {len(SYMBOLS)} عملة...')

        for symbol in SYMBOLS:
            try:
                data = analyze_symbol(symbol)

                if data['signal'] == 'ERROR':
                    continue

                coin = symbol.replace('USDT', '')
                log.info(
                    f'  {coin}: RSI={data["rsi"]} | '
                    f'MACD={data["macd_hist"]:+.6f} | '
                    f'{data["signal"]}'
                )

                # أرسل إشعار فقط عند BUY أو SELL وإذا تغيرت الإشارة
                if data['signal'] in ('BUY', 'SELL'):
                    if should_send_signal(symbol, data['signal']):
                        send_signal(data)

                time.sleep(0.5)  # تجنب rate limit

            except Exception as e:
                log.error(f'خطأ في {symbol}: {e}')

        log.info(f'⏰ انتظار {SCAN_INTERVAL} ثانية...')
        time.sleep(SCAN_INTERVAL)


if __name__ == '__main__':
    run_bot()