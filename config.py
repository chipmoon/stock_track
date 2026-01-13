# config.py

# Format mới: (Symbol, Name, Exchange, Screener)
# Nếu Crypto: Exchange='BINANCE', Screener='crypto'
# Nếu Vàng/Forex: Exchange='OANDA' (hoặc FX_IDC), Screener='cfd' (hoặc forex)

COINS = [
    # Crypto
    ("BTCUSDT", "Bitcoin", "BINANCE", "crypto"),
    ("ETHUSDT", "Ethereum", "BINANCE", "crypto"),
    ("SOLUSDT", "Solana", "BINANCE", "crypto"),
    ("LINKUSDT", "Chainlink", "BINANCE", "crypto"),
    
    # Gold / Forex
    ("XAUUSD", "Gold Spot", "OANDA", "cfd"), 
    # Mẹo: Dùng screener='cfd' cho OANDA/FXCM thường ổn định hơn 'forex' với library này
]

# Các biến mặc định cũ (giữ để fallback)
EXCHANGE = "BINANCE"
SCREENER = "crypto"

TAB_LATEST = "latest"
TAB_HISTORY = "history"
