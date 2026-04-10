import requests
import time
import os
from dotenv import load_dotenv

# تحميل مفاتيح السرية
load_dotenv()

# إعدادات تليجرام
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- فلتر الحوكمة الشرعية (Shariah Compliance) ---
# ملاحظة: هذه قائمة أولية، يفضل تحديثها دورياً من مصادر موثوقة
HALAL_KEYWORDS = ['gold', 'stable', 'realestate', 'tech', 'utility']
BANNED_KEYWORDS = ['casino', 'bet', 'gamble', 'win', 'lotto', 'dice', 'shiba', 'doge', 'pepe']

def is_shariah_compliant(pair_data):
    """فحص شرعية العملة بناءً على الاسم والوصف والسيولة"""
    name = pair_data.get('baseToken', {}).get('name', '').lower()
    symbol = pair_data.get('baseToken', {}).get('symbol', '').lower()
    
    # 1. فحص الكلمات المحرمة في الاسم (قمار، ميم غير هادف، إلخ)
    for word in BANNED_KEYWORDS:
        if word in name or word in symbol:
            return False
            
    # 2. فحص السيولة (تجنب العملات الوهمية أو غسيل الأموال)
    liquidity = pair_data.get('liquidity', {}).get('usd', 0)
    if liquidity < 10000:  # الحد الأدنى للسيولة 10 آلاف دولار لضمان الجدية
        return False
        
    return True

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"خطأ في إرسال تليجرام: {e}")

def scan_dex_screener():
    """رادار DexScreener للسيولة والتريند"""
    print("🔍 جاري مسح DexScreener عن الفرص الحلال...")
    # رابط لجلب العملات الأكثر تداولاً (Trending) على شبكة Solana كمثال
    url = "https://api.dexscreener.com/latest/dex/search?q=solana" 
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            pairs = response.json().get('pairs', [])
            for pair in pairs[:10]:  # فحص أعلى 10 نتائج
                price_change = pair.get('priceChange', {}).get('h1', 0)
                volume = pair.get('volume', {}).get('h1', 0)
                
                # شرط التنبيه: ارتفاع سعري > 10% وحجم تداول جيد وفلتر حلال
                if price_change > 10 and volume > 50000:
                    if is_shariah_compliant(pair):
                        msg = (
                            f"🚀 *فرصة DexScreener حلال*\n"
                            f"💎 العملة: {pair['baseToken']['name']} ({pair['baseToken']['symbol']})\n"
                            f"📈 التغير (1h): {price_change}%\n"
                            f"💰 السيولة: ${pair['liquidity']['usd']:,.0f}\n"
                            f"📊 حجم التداول: ${volume:,.0f}\n"
                            f"🔗 الرابط: {pair['url']}"
                        )
                        send_telegram_msg(msg)
                        print(f"✅ تم العثور على فرصة: {pair['baseToken']['symbol']}")
        else:
            print("⚠️ فشل الاتصال بـ DexScreener")
    except Exception as e:
        print(f"❌ خطأ تقني: {e}")

# تشغيل الرادار
if __name__ == "__main__":
    while True:
        scan_dex_screener()
        time.sleep(300)  # المسح كل 5 دقائق لراحة المعالج