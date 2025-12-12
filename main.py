import ccxt
import asyncio
import time
from fastapi import FastAPI
import uvicorn

# ===========================
#   CONFIG (EDIT YANG PERLU)
# ===========================

API_KEY = ""
API_SECRET = ""
PASSPHRASE = ""

SYMBOL = "DOGE/USDT"
TRADE_USDT = 1.0          # jumlah USDT per trade
SMA_PERIOD = 8            # jumlah sampel harga
INTERVAL = 5              # detik antar cek harga
BUY_BELOW = 0.10          # beli jika harga 0.10% di bawah SMA
SELL_ABOVE = 0.20         # jual jika harga 0.20% di atas SMA
MAX_POS = 5               # max jumlah posisi (kelipatan DOGE)

# ===========================
#   FASTAPI SERVER
# ===========================

app = FastAPI()
last_prices = []
position = 0
running = False

# ===========================
#  CONNECT EXCHANGE (OKX)
# ===========================

def get_client():
    return ccxt.okx({
        "apiKey": API_KEY,
        "secret": API_SECRET,
        "password": PASSPHRASE,
        "enableRateLimit": True,
    })

# ===========================
#  SMA CALCULATOR
# ===========================

def sma(values):
    if len(values) == 0:
        return 0
    return sum(values) / len(values)

# ===========================
#  AUTO TRADE LOOP
# ===========================

async def auto_loop():
    global running, last_prices, position

    client = get_client()
    print("[core] Starting MoonBot AGR SAFE mode...")

    while running:
        try:
            # GET PRICE
            ticker = client.fetch_ticker(SYMBOL)
            price = ticker["last"]
            last_prices.append(price)
            last_prices = last_prices[-SMA_PERIOD:]

            avg = sma(last_prices)

            dev = (price - avg) / avg * 100

            # BUY
            if dev <= -BUY_BELOW and position < MAX_POS:
                amount = TRADE_USDT / price
                client.create_market_buy_order(SYMBOL, amount)
                position += amount
                print(f"[LIVE BUY] {amount} at price {price}")

            # SELL
            if dev >= SELL_ABOVE and position > 0:
                client.create_market_sell_order(SYMBOL, position)
                print(f"[LIVE SELL] {position} at price {price}")
                position = 0

            print(f"[loop] price={price:.6f} SMA={avg:.6f} dev={dev:.3f}% pos={position}")

        except Exception as e:
            print("[ERR]", e)

        await asyncio.sleep(INTERVAL)

# ===========================
# FASTAPI ROUTES
# ===========================

@app.get("/")
def home():
    return {
        "status": "MoonBot AGR RUNNING",
        "symbol": SYMBOL,
        "position": position,
        "latest_price": last_prices[-1] if last_prices else None
    }

@app.get("/start")
def start():
    global running
    if running:
        return {"msg": "Already running"}

    running = True
    asyncio.create_task(auto_loop())
    return {"msg": "Bot started"}

@app.get("/stop")
def stop():
    global running
    running = False
    return {"msg": "Bot stopped"}

# ===========================
# UVICORN START
# ===========================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
