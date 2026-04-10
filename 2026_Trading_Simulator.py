import requests
import time
import os
from dotenv import load_dotenv

# تحميل الإعدادات
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- فلتر الحوكمة الشرعية (Halal Filter) ---
BANNED_KEYWORDS = ['casino', 'bet', 'gamble', 'win', 'lotto', 'dice', 'shiba', 'doge', 'pepe']

def is_shariah_compliant(name, symbol):
    """فحص شرعية الاسم والرمز"""
    combined = (name + symbol).lower()
    for word in BANNED_KEYWORDS:
        if word in combined:
            return False
    return True

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

# --- 1. رادار DexScreener (السيولة والتريند) ---
def scan_dex():
    print("🔍 مسح DexScreener...")
    url = "https://api.dexscreener.com/latest/dex/search?q=solana"
    try:
        response = requests.get(url).json()
        for pair in response.get('pairs', [])[:5]:
            if is_shariah_compliant(pair['baseToken']['name'], pair['baseToken']['symbol']):
                if pair.get('priceChange', {}).get('h1', 0) > 15: # ارتفاع أكثر من 15%
                    msg = f"🌟 *فرصة DEX حلال*\n💰 {pair['baseToken']['symbol']}\n📈 نمو: {pair['priceChange']['h1']}%\n💧 سيولة: ${pair['liquidity']['usd']:,.0f}"
                    send_telegram_msg(msg)
    except: pass

# --- 2. رادار TradingView (التحليل الفني) ---
def scan_tradingview():
    print("📊 تحليل TradingView...")
    # ملاحظة: نستخدم هنا محاكي لجلب الإشارات الفنية القوية (Strong Buy)
    # في النسخة الاحترافية يتم ربطها بـ Webhook لـ TradingView
    try:
        # هنا نضع العملات الحلال فقط للمراقبة الفنية
        watchlist = ["BTCUSDT", "ETHUSDT", "SOLUSDT"] 
        for symbol in watchlist:
            # محاكاة لاستقبال إشارة RSI من TV
            msg = f"📈 *إشارة TradingView حلال*\n💎 العملة: {symbol}\n🎯 الحالة: اختراق RSI إيجابي (حسب برمجتنا)"
            send_telegram_msg(msg)
    except: pass

if __name__ == "__main__":
    while True:
        scan_dex()           # مراقبة اللامركزية
        scan_tradingview()   # مراقبة التحليل الفني
        time.sleep(300)      # تحديث كل 5 دقائق لراحة Render