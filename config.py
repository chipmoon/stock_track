# config.py

# === TIMEFRAMES (Only use supported intervals) ===
CRYPTO_TIMEFRAMES = ["4H", "1D", "1W"]
STOCK_TIMEFRAMES = ["1D", "1W", "1M"]

# === TAB NAMES ===
TAB_CONFIG = "config"
TAB_CRYPTO = "Crypto"
TAB_STOCK = "Stock"
TAB_HISTORY = "history"
TAB_DASHBOARD_STOCK = "Dashboard_Stock"
TAB_DASHBOARD_CRYPTO = "Dashboard_Crypto"

# === GLOBAL VARIABLES (populated from Google Sheet ONLY) ===
CRYPTO_COINS = []
STOCK_COINS = []
FOREX_METALS = []


def load_config_from_sheet(ss):
    """
    Load configuration from Google Sheet 'config' tab
    Expected format (case-insensitive):

    Row 1: [Symbol, Name, Exchange, Screener, Type] or [Type, Symbol, Name, Exchange, Screener]
    Row 2+: Data rows

    Example:
    BTCUSDT | Bitcoin | Binance | crypto | crypto
    2330 | TSMC | TWSE | taiwan | stock
    BSR | Binh Son Refining | HOSE | vietnam | stock
    """
    global CRYPTO_COINS, STOCK_COINS, FOREX_METALS

    try:
        print("📋 Loading config from Google Sheet 'config' tab...")
        ws = ss.worksheet(TAB_CONFIG)
        all_rows = ws.get_all_values()

        if len(all_rows) < 2:
            raise Exception("Config tab is empty or only has header")

        # Parse header to find column indices
        header = [h.strip().lower() for h in all_rows[0]]

        # Find column indices (flexible order)
        try:
            symbol_idx = header.index("symbol")
            name_idx = header.index("name")
            exchange_idx = header.index("exchange")
            screener_idx = header.index("screener")

            # Type column is optional (can be inferred from screener)
            type_idx = header.index("type") if "type" in header else None
        except ValueError as e:
            raise Exception(f"Missing required column in header: {e}")

        # Skip header row, process data
        config_rows = all_rows[1:]

        crypto_list = []
        stock_list = []
        forex_list = []

        for i, row in enumerate(config_rows, start=2):
            if len(row) < 4:
                print(f"⚠️ Row {i}: Incomplete data, skipping")
                continue

            try:
                symbol = row[symbol_idx].strip()
                name = row[name_idx].strip()
                exchange = row[exchange_idx].strip()
                screener = row[screener_idx].strip()

                # Skip empty rows
                if not symbol or not name:
                    continue

                # Determine asset type
                if type_idx is not None and len(row) > type_idx:
                    asset_type = row[type_idx].strip().lower()
                else:
                    # Infer from screener if Type column missing
                    asset_type = screener.lower()

                entry = (symbol, name, exchange, screener)

                # === CATEGORIZE BASED ON TYPE/SCREENER ===

                # Crypto assets
                if asset_type in ["crypto", "cryptocurrency"]:
                    crypto_list.append(entry)
                    print(f"   ✅ Crypto: {symbol} ({name})")

                # Stock markets (Taiwan + Vietnam + Other)
                elif asset_type in [
                    "stock", 
                    # Taiwan exchanges
                    "taiwan", "twse", "tpex",
                    # Vietnam exchanges
                    "vietnam", "hose", "hnx", "upcom",
                    # US exchanges (bonus)
                    "america", "nasdaq", "nyse"
                ]:
                    stock_list.append(entry)
                    print(f"   ✅ Stock: {symbol} ({name}) [{exchange}]")

                # Forex/Metals/CFDs
                elif asset_type in ["forex", "metal", "cfd", "oanda", "fx"]:
                    forex_list.append(entry)
                    print(f"   ✅ Forex/Metal: {symbol} ({name})")

                else:
                    print(f"   ⚠️ Unknown type '{asset_type}' for {symbol}, skipping")

            except Exception as e:
                print(f"⚠️ Row {i}: Error parsing - {e}")
                continue

        # Update global variables
        CRYPTO_COINS = crypto_list
        STOCK_COINS = stock_list
        FOREX_METALS = forex_list

        print(f"\n✅ Loaded from config tab:")
        print(f"   - Crypto: {len(CRYPTO_COINS)} symbols")
        print(f"   - Stock: {len(STOCK_COINS)} symbols")
        print(f"   - Forex/Metals: {len(FOREX_METALS)} symbols")

        if not CRYPTO_COINS and not STOCK_COINS:
            raise Exception("No valid symbols loaded from config tab!")

    except Exception as e:
        print(f"❌ Error reading config tab: {e}")
        raise RuntimeError(f"Cannot load config from Google Sheet: {e}")


def ensure_config_tab(ss):
    """
    Create config tab if it doesn't exist with example format
    """
    try:
        ws = ss.worksheet(TAB_CONFIG)
        print(f"✅ Config tab exists")
        return ws
    except:
        print(f"📝 Creating config tab with example format...")
        ws = ss.add_worksheet(title=TAB_CONFIG, rows=100, cols=5)

        # Header + Example data
        example_data = [
            ["Symbol", "Name", "Exchange", "Screener", "Type"],
            ["BTCUSDT", "Bitcoin", "BINANCE", "crypto", "crypto"],
            ["ETHUSDT", "Ethereum", "BINANCE", "crypto", "crypto"],
            ["2330", "TSMC", "TWSE", "taiwan", "stock"],
            ["2455", "Visual Photonics", "TWSE", "taiwan", "stock"],
            ["BSR", "Binh Son Refining", "HOSE", "vietnam", "stock"],
            ["XAUUSD", "Gold", "OANDA", "cfd", "forex"],
        ]

        ws.update("A1", example_data)
        print(f"✅ Config tab created with example data")
        print(f"⚠️ Please customize the config tab and run again!")
        return ws
