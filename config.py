# config.py

# === TIMEFRAMES (Only use supported intervals) ===
CRYPTO_TIMEFRAMES = ["4H", "1D", "1W"]
STOCK_TIMEFRAMES = ["1D", "1W", "1M"]

# === TAB NAMES ===
TAB_CONFIG = "config"
TAB_CRYPTO = "Crypto"
TAB_STOCK_TW = "Stock_TW"     # Taiwan stocks
TAB_STOCK_VN = "Stock_VN"     # Vietnam stocks
TAB_HISTORY = "history"
TAB_DASHBOARD_STOCK_TW = "Dashboard_Stock_TW"
TAB_DASHBOARD_STOCK_VN = "Dashboard_Stock_VN"
TAB_DASHBOARD_CRYPTO = "Dashboard_Crypto"

# === GLOBAL VARIABLES (populated from Google Sheet ONLY) ===
CRYPTO_COINS = []
STOCK_COINS_TW = []    # Taiwan stocks
STOCK_COINS_VN = []    # Vietnam stocks
FOREX_METALS = []


def load_config_from_sheet(ss):
    """
    Load configuration from Google Sheet 'config' tab
    Now separates Taiwan and Vietnam stocks into different lists
    """
    global CRYPTO_COINS, STOCK_COINS_TW, STOCK_COINS_VN, FOREX_METALS

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
            type_idx = header.index("type") if "type" in header else None
        except ValueError as e:
            raise Exception(f"Missing required column in header: {e}")

        # Skip header row, process data
        config_rows = all_rows[1:]

        crypto_list = []
        stock_tw_list = []
        stock_vn_list = []
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
                    asset_type = screener.lower()

                entry = (symbol, name, exchange, screener)

                # === CATEGORIZE BY TYPE ===

                # Crypto
                if asset_type in ["crypto", "cryptocurrency"]:
                    crypto_list.append(entry)
                    print(f"   ✅ Crypto: {symbol} ({name})")

                # Taiwan stocks
                elif asset_type in ["taiwan", "twse", "tpex"]:
                    stock_tw_list.append(entry)
                    print(f"   ✅ Stock TW: {symbol} ({name}) [{exchange}]")

                # Vietnam stocks
                elif asset_type in ["vietnam", "hose", "hnx", "upcom"]:
                    stock_vn_list.append(entry)
                    print(f"   ✅ Stock VN: {symbol} ({name}) [{exchange}]")

                # Generic "stock" type - try to determine by exchange
                elif asset_type == "stock":
                    if exchange.upper() in ["TWSE", "TPEX"]:
                        stock_tw_list.append(entry)
                        print(f"   ✅ Stock TW: {symbol} ({name}) [{exchange}]")
                    elif exchange.upper() in ["HOSE", "HNX", "UPCOM"]:
                        stock_vn_list.append(entry)
                        print(f"   ✅ Stock VN: {symbol} ({name}) [{exchange}]")
                    else:
                        print(f"   ⚠️ Stock {symbol} has unknown exchange '{exchange}', skipping")

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
        STOCK_COINS_TW = stock_tw_list
        STOCK_COINS_VN = stock_vn_list
        FOREX_METALS = forex_list

        print(f"\n✅ Loaded from config tab:")
        print(f"   - Crypto: {len(CRYPTO_COINS)} symbols")
        print(f"   - Stock TW: {len(STOCK_COINS_TW)} symbols")
        print(f"   - Stock VN: {len(STOCK_COINS_VN)} symbols")
        print(f"   - Forex/Metals: {len(FOREX_METALS)} symbols")

        if not CRYPTO_COINS and not STOCK_COINS_TW and not STOCK_COINS_VN:
            raise Exception("No valid symbols loaded from config tab!")

    except Exception as e:
        print(f"❌ Error reading config tab: {e}")
        raise RuntimeError(f"Cannot load config from Google Sheet: {e}")


def ensure_config_tab(ss):
    """Create config tab if it doesn't exist"""
    try:
        ws = ss.worksheet(TAB_CONFIG)
        print(f"✅ Config tab exists")
        return ws
    except:
        print(f"📝 Creating config tab with example format...")
        ws = ss.add_worksheet(title=TAB_CONFIG, rows=100, cols=4)

        example_data = [
            ["Symbol", "Name", "Exchange", "Screener"],
            ["BTCUSDT", "Bitcoin", "BINANCE", "crypto"],
            ["ETHUSDT", "Ethereum", "BINANCE", "crypto"],
            ["XAUUSD", "Gold", "OANDA", "cfd"],
            ["2330", "TSMC", "TWSE", "taiwan"],
            ["2455", "Visual Photonics", "TWSE", "taiwan"],
            ["BSR", "Binh Son Refining", "HOSE", "vietnam"],
            ["FPT", "FPT Corp", "HOSE", "vietnam"],
        ]

        ws.update("A1", example_data)
        print(f"✅ Config tab created with example data")
        return ws
