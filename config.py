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

# Forex/Metals (can be in either category)
FOREX_METALS = [
    ("XAUUSD", "Gold", "OANDA", "cfd"),
    ("EURUSD", "Euro", "FX_IDC", "forex"),
]

# Timeframes for each asset class
CRYPTO_TIMEFRAMES = ["4H", "1D", "3D", "1W"]
STOCK_TIMEFRAMES = ["1D", "3D", "1W", "1M"]

# Tab names
TAB_CRYPTO = "Crypto"
TAB_STOCK = "Stock"
TAB_HISTORY = "history"
TAB_DASHBOARD = "Dashboard"
