# config.py

# Crypto symbols with fast timeframes
CRYPTO_COINS = [
    ("BTCUSDT", "Bitcoin", "BINANCE", "crypto"),
    ("ETHUSDT", "Ethereum", "BINANCE", "crypto"),
    ("SOLUSDT", "Solana", "BINANCE", "crypto"),
    ("PEPEUSDT", "PEPE", "BINANCE", "crypto"),
    ("LINKUSDT", "Chainlink", "BINANCE", "crypto"),
    ("BNBUSDT", "Binance Coin", "BINANCE", "crypto"),
]

# Stock symbols with slower timeframes
STOCK_COINS = [
    ("2455", "Visual Photonics", "TWSE", "taiwan"),
    ("8096", "CoAsia", "TPEX", "taiwan"),
    ("2330", "TSMC", "TWSE", "taiwan"),
]

# Forex/Metals (optional - can add later)
FOREX_METALS = [
    ("XAUUSD", "Gold", "OANDA", "cfd"),
    ("EURUSD", "Euro", "FX_IDC", "forex"),
]

# === TIMEFRAMES (Only use supported intervals) ===
# Crypto: Fast trading
CRYPTO_TIMEFRAMES = ["4H", "1D", "1W"]

# Stock: Longer term  
STOCK_TIMEFRAMES = ["1D", "1W", "1M"]

# === TAB NAMES ===
TAB_CRYPTO = "Crypto"
TAB_STOCK = "Stock"
TAB_HISTORY = "history"
TAB_DASHBOARD_STOCK = "Dashboard_Stock"
TAB_DASHBOARD_CRYPTO = "Dashboard_Crypto"
