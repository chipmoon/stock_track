# config.py

# === DEFAULT CONFIGURATION (Fallback if Google Sheet config not available) ===

# Default crypto symbols
DEFAULT_CRYPTO_COINS = [
    ("BTCUSDT", "Bitcoin", "BINANCE", "crypto"),
    ("ETHUSDT", "Ethereum", "BINANCE", "crypto"),
    ("SOLUSDT", "Solana", "BINANCE", "crypto"),
    ("PEPEUSDT", "PEPE", "BINANCE", "crypto"),
    ("LINKUSDT", "Chainlink", "BINANCE", "crypto"),
    ("BNBUSDT", "Binance Coin", "BINANCE", "crypto"),
]

# Default stock symbols
DEFAULT_STOCK_COINS = [
    ("2455", "Visual Photonics", "TWSE", "taiwan"),
    ("8096", "CoAsia", "TPEX", "taiwan"),
    ("2330", "TSMC", "TWSE", "taiwan"),
]

# Default forex/metals (optional)
DEFAULT_FOREX_METALS = [
    ("XAUUSD", "Gold", "OANDA", "cfd"),
    ("EURUSD", "Euro", "FX_IDC", "forex"),
]

# === TIMEFRAMES (Only use supported intervals) ===
# Crypto: Fast trading
CRYPTO_TIMEFRAMES = ["4H", "1D", "1W"]

# Stock: Longer term  
STOCK_TIMEFRAMES = ["1D", "1W", "1M"]

# === TAB NAMES ===
TAB_CONFIG = "config"
TAB_CRYPTO = "Crypto"
TAB_STOCK = "Stock"
TAB_HISTORY = "history"
TAB_DASHBOARD_STOCK = "Dashboard_Stock"
TAB_DASHBOARD_CRYPTO = "Dashboard_Crypto"

# === GLOBAL VARIABLES (Will be populated from Google Sheet) ===
CRYPTO_COINS = []
STOCK_COINS = []
FOREX_METALS = []


def load_config_from_sheet(ss):
    """
    Load configuration from Google Sheet 'config' tab
    Expected format:

    Row 1: [Type, Symbol, Name, Exchange, Screener]
    Row 2: [crypto, BTCUSDT, Bitcoin, BINANCE, crypto]
    Row 3: [stock, 2330, TSMC, TWSE, taiwan]
    ...
    """
    global CRYPTO_COINS, STOCK_COINS, FOREX_METALS

    try:
        print("📋 Loading config from Google Sheet...")
        ws = ss.worksheet(TAB_CONFIG)
        all_rows = ws.get_all_values()

        if len(all_rows) < 2:
            print("⚠️ Config tab empty or only has header. Using default config.")
            CRYPTO_COINS = DEFAULT_CRYPTO_COINS
            STOCK_COINS = DEFAULT_STOCK_COINS
            FOREX_METALS = DEFAULT_FOREX_METALS
            return

        # Skip header row
        config_rows = all_rows[1:]

        crypto_list = []
        stock_list = []
        forex_list = []

        for row in config_rows:
            if len(row) < 5:
                continue  # Skip incomplete rows

            asset_type = row[0].strip().lower()
            symbol = row[1].strip()
            name = row[2].strip()
            exchange = row[3].strip()
            screener = row[4].strip()

            # Skip empty rows
            if not symbol or not name:
                continue

            entry = (symbol, name, exchange, screener)

            if asset_type == "crypto":
                crypto_list.append(entry)
            elif asset_type == "stock":
                stock_list.append(entry)
            elif asset_type in ["forex", "metal", "cfd"]:
                forex_list.append(entry)

        # Update global variables
        CRYPTO_COINS = crypto_list if crypto_list else DEFAULT_CRYPTO_COINS
        STOCK_COINS = stock_list if stock_list else DEFAULT_STOCK_COINS
        FOREX_METALS = forex_list if forex_list else DEFAULT_FOREX_METALS

        print(f"✅ Loaded from config tab:")
        print(f"   - Crypto: {len(CRYPTO_COINS)} symbols")
        print(f"   - Stock: {len(STOCK_COINS)} symbols")
        print(f"   - Forex/Metals: {len(FOREX_METALS)} symbols")

    except Exception as e:
        print(f"⚠️ Error reading config tab: {e}")
        print("   Using default configuration...")
        CRYPTO_COINS = DEFAULT_CRYPTO_COINS
        STOCK_COINS = DEFAULT_STOCK_COINS
        FOREX_METALS = DEFAULT_FOREX_METALS


def ensure_config_tab(ss):
    """
    Create config tab if it doesn't exist, populate with default values
    """
    try:
        ws = ss.worksheet(TAB_CONFIG)
        print(f"✅ Config tab exists")
    except:
        print(f"📝 Creating config tab with default values...")
        ws = ss.add_worksheet(title=TAB_CONFIG, rows=100, cols=5)

        # Header
        header = ["Type", "Symbol", "Name", "Exchange", "Screener"]

        # Default data
        default_data = [header]

        # Add crypto
        for item in DEFAULT_CRYPTO_COINS:
            default_data.append(["crypto", item[0], item[1], item[2], item[3]])

        # Add stocks
        for item in DEFAULT_STOCK_COINS:
            default_data.append(["stock", item[0], item[1], item[2], item[3]])

        # Add forex/metals
        for item in DEFAULT_FOREX_METALS:
            default_data.append(["forex", item[0], item[1], item[2], item[3]])

        ws.update("A1", default_data)
        print(f"✅ Config tab created with {len(default_data)-1} default entries")
