import requests
import os
import time
from datetime import datetime

# --- कॉन्फ़िगरेशन ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# कितने प्रतिशत OI बदलाव पर अलर्ट भेजना है
OI_SPIKE_THRESHOLD = 5.0
TIMEFRAME = "5m"
LIMIT = 12

# जिन कॉइन्स को track करना है
SYMBOLS_TO_WATCH = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]

def send_telegram_alert(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram config missing")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        print(f"📤 Alert sent: {r.status_code}")
    except Exception as e:
        print(f"❌ Telegram error: {e}")

def get_current_price(symbol):
    url = "https://fapi.binance.com/fapi/v1/ticker/price"
    try:
        r = requests.get(url, params={"symbol": symbol}, timeout=10)
        return float(r.json()["price"])
    except:
        return None

def check_oi_spike(symbol):
    url = "https://fapi.binance.com/futures/data/openInterestHist"
    params = {"symbol": symbol, "period": TIMEFRAME, "limit": LIMIT}
    
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        
        if len(data) < 2:
            print(f"⚠️ {symbol}: Not enough data")
            return
        
        oldest_oi = float(data[0]['sumOpenInterest'])
        latest_oi = float(data[-1]['sumOpenInterest'])
        
        if oldest_oi == 0:
            return
        
        oi_change = ((latest_oi - oldest_oi) / oldest_oi) * 100
        price = get_current_price(symbol)
        
        print(f"📊 {symbol}: OI change = {oi_change:.2f}% | Price = {price}")
        
        if abs(oi_change) >= OI_SPIKE_THRESHOLD:
            if oi_change > 0:
                direction = "🟢 OI बढ़ रहा है (Long/Short Build-up)"
                emoji = "📈"
            else:
                direction = "🔴 OI घट रहा है (Unwinding/Covering)"
                emoji = "📉"
            
            alert = (
                f"{emoji} *{symbol} OI स्पाइक अलर्ट!*\n\n"
                f"*बदलाव:* {oi_change:+.2f}%\n"
                f"*दिशा:* {direction}\n"
                f"*समय सीमा:* {TIMEFRAME}\n"
                f"*वर्तमान OI:* {latest_oi:,.0f}\n"
                f"*वर्तमान प्राइस:* ${price:,.2f}\n"
                f"*समय:* {datetime.now().strftime('%d-%m-%Y %H:%M')}"
            )
            send_telegram_alert(alert)
    
    except Exception as e:
        print(f"❌ {symbol} error: {e}")

def main():
    print(f"🚀 Started OI Monitor at {datetime.now()}")
    for symbol in SYMBOLS_TO_WATCH:
        check_oi_spike(symbol)
        time.sleep(0.3)
    print("✅ All checks complete")

if __name__ == "__main__":
    main()
