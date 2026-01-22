# sheets_writer.py
import gspread
from google.oauth2.service_account import Credentials

def open_spreadsheet(sa_json_path: str, sheet_id: str):
    """Connect to Google Sheets using modern google-auth"""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    creds = Credentials.from_service_account_file(sa_json_path, scopes=scopes)
    client = gspread.authorize(creds)
    return client.open_by_key(sheet_id)


def ensure_tab(ss, tab_name: str):
    """Get or create worksheet"""
    try:
        ws = ss.worksheet(tab_name)
        print(f"✅ Tab '{tab_name}' exists")
        return ws
    except:
        ws = ss.add_worksheet(title=tab_name, rows=500, cols=20)
        print(f"✅ Created tab '{tab_name}'")
        return ws


def delete_tab_if_exists(ss, tab_name: str):
    """Delete a tab if it exists"""
    try:
        ws = ss.worksheet(tab_name)
        ss.del_worksheet(ws)
        print(f"🗑️ Deleted old tab '{tab_name}'")
    except:
        print(f"ℹ️ Tab '{tab_name}' doesn't exist (nothing to delete)")


def write_table(ws, data):
    """Write data with header to worksheet (clears existing data)"""
    ws.clear()
    ws.update(range_name="A1", values=data)
    print(f"✅ Written {len(data)} rows to '{ws.title}'")


def append_rows(ws, rows):
    """Append rows to existing worksheet"""
    ws.append_rows(rows, value_input_option="USER_ENTERED")
    print(f"✅ Appended {len(rows)} rows to '{ws.title}'")


def update_dashboard_crypto(ss, crypto_data):
    """
    Update Dashboard_Crypto with summary and top signals
    crypto_data format: [header, row1, row2, ...]
    """
    from config import TAB_DASHBOARD_CRYPTO

    ws = ensure_tab(ss, TAB_DASHBOARD_CRYPTO)
    ws.clear()

    header = crypto_data[0] if crypto_data else []
    rows = crypto_data[1:] if len(crypto_data) > 1 else []

    dashboard_content = []
    dashboard_content.append(["📊 CRYPTO DASHBOARD"])
    dashboard_content.append([])

    if rows:
        symbol_signals = {}
        for r in rows:
            symbol = r[0]
            signal = str(r[9])
            if symbol not in symbol_signals:
                symbol_signals[symbol] = {"signal": signal, "confidence": r[10]}
            else:
                if r[10] > symbol_signals[symbol]["confidence"]:
                    symbol_signals[symbol] = {"signal": signal, "confidence": r[10]}

        strong_buy = len([s for s in symbol_signals.values() if "STRONG BUY" in s["signal"]])
        dip_buy = len([s for s in symbol_signals.values() if "DIP BUY" in s["signal"]])
        hold = len([s for s in symbol_signals.values() if "HOLD" in s["signal"] and "STRONG BUY" not in s["signal"]])
        sell = len([s for s in symbol_signals.values() if "SELL" in s["signal"]])

        dashboard_content.append(["=== SIGNAL SUMMARY (Unique Symbols) ==="])
        dashboard_content.append(["🚀 Strong Buy:", strong_buy])
        dashboard_content.append(["📉 Dip Buy:", dip_buy])
        dashboard_content.append(["✅ Hold:", hold])
        dashboard_content.append(["🔴 Sell:", sell])
        dashboard_content.append(["📊 Total Symbols:", len(symbol_signals)])
        dashboard_content.append([])

        dashboard_content.append(["=== TOP CRYPTO OPPORTUNITIES ==="])
        dashboard_content.append(header)

        top_signals = sorted(
            [r for r in rows if r[10] >= 75],
            key=lambda x: x[10],
            reverse=True
        )[:10]

        dashboard_content.extend(top_signals)

        if not top_signals:
            dashboard_content.append(["No high-confidence signals at the moment"])
    else:
        dashboard_content.append(["No crypto data available"])

    write_table(ws, dashboard_content)
    print(f"✅ Dashboard_Crypto updated: {len(rows)} signals from {len(symbol_signals) if rows else 0} unique symbols")


def update_dashboard_stock_tw(ss, stock_tw_data):
    """
    Update Dashboard_Stock_TW with Taiwan stock signals
    """
    from config import TAB_DASHBOARD_STOCK_TW

    ws = ensure_tab(ss, TAB_DASHBOARD_STOCK_TW)
    ws.clear()

    header = stock_tw_data[0] if stock_tw_data else []
    rows = stock_tw_data[1:] if len(stock_tw_data) > 1 else []

    dashboard_content = []
    dashboard_content.append(["📈 TAIWAN STOCK DASHBOARD"])
    dashboard_content.append([])

    if rows:
        symbol_signals = {}
        for r in rows:
            symbol = r[0]
            signal = str(r[9])
            if symbol not in symbol_signals:
                symbol_signals[symbol] = {"signal": signal, "confidence": r[10]}
            else:
                if r[10] > symbol_signals[symbol]["confidence"]:
                    symbol_signals[symbol] = {"signal": signal, "confidence": r[10]}

        strong_buy = len([s for s in symbol_signals.values() if "STRONG BUY" in s["signal"]])
        dip_buy = len([s for s in symbol_signals.values() if "DIP BUY" in s["signal"]])
        extreme_value = len([s for s in symbol_signals.values() if "EXTREME VALUE" in s["signal"]])
        hold = len([s for s in symbol_signals.values() if "HOLD" in s["signal"] and "STRONG BUY" not in s["signal"]])
        sell = len([s for s in symbol_signals.values() if "SELL" in s["signal"]])

        dashboard_content.append(["=== TAIWAN STOCK SIGNALS (Unique Symbols) ==="])
        dashboard_content.append(["🚀 Strong Buy:", strong_buy])
        dashboard_content.append(["📉 Dip Buy:", dip_buy])
        dashboard_content.append(["💎 Extreme Value:", extreme_value])
        dashboard_content.append(["✅ Hold:", hold])
        dashboard_content.append(["🔴 Sell:", sell])
        dashboard_content.append(["📊 Total Symbols:", len(symbol_signals)])
        dashboard_content.append([])

        dashboard_content.append(["=== TOP TAIWAN OPPORTUNITIES ==="])
        dashboard_content.append(header)

        top_signals = sorted(
            [r for r in rows if r[10] >= 70],
            key=lambda x: x[10],
            reverse=True
        )[:10]

        dashboard_content.extend(top_signals)

        if not top_signals:
            dashboard_content.append(["No high-confidence signals at the moment"])
    else:
        dashboard_content.append(["No Taiwan stock data available"])

    write_table(ws, dashboard_content)
    print(f"✅ Dashboard_Stock_TW updated: {len(rows)} signals from {len(symbol_signals) if rows else 0} unique symbols")


def update_dashboard_stock_vn(ss, stock_vn_data):
    """
    Update Dashboard_Stock_VN with Vietnam stock signals
    """
    from config import TAB_DASHBOARD_STOCK_VN

    ws = ensure_tab(ss, TAB_DASHBOARD_STOCK_VN)
    ws.clear()

    header = stock_vn_data[0] if stock_vn_data else []
    rows = stock_vn_data[1:] if len(stock_vn_data) > 1 else []

    dashboard_content = []
    dashboard_content.append(["📈 VIETNAM STOCK DASHBOARD"])
    dashboard_content.append([])

    if rows:
        symbol_signals = {}
        for r in rows:
            symbol = r[0]
            signal = str(r[9])
            if symbol not in symbol_signals:
                symbol_signals[symbol] = {"signal": signal, "confidence": r[10]}
            else:
                if r[10] > symbol_signals[symbol]["confidence"]:
                    symbol_signals[symbol] = {"signal": signal, "confidence": r[10]}

        strong_buy = len([s for s in symbol_signals.values() if "STRONG BUY" in s["signal"]])
        dip_buy = len([s for s in symbol_signals.values() if "DIP BUY" in s["signal"]])
        extreme_value = len([s for s in symbol_signals.values() if "EXTREME VALUE" in s["signal"]])
        hold = len([s for s in symbol_signals.values() if "HOLD" in s["signal"] and "STRONG BUY" not in s["signal"]])
        sell = len([s for s in symbol_signals.values() if "SELL" in s["signal"]])

        dashboard_content.append(["=== VIETNAM STOCK SIGNALS (Unique Symbols) ==="])
        dashboard_content.append(["🚀 Strong Buy:", strong_buy])
        dashboard_content.append(["📉 Dip Buy:", dip_buy])
        dashboard_content.append(["💎 Extreme Value:", extreme_value])
        dashboard_content.append(["✅ Hold:", hold])
        dashboard_content.append(["🔴 Sell:", sell])
        dashboard_content.append(["📊 Total Symbols:", len(symbol_signals)])
        dashboard_content.append([])

        dashboard_content.append(["=== TOP VIETNAM OPPORTUNITIES ==="])
        dashboard_content.append(header)

        top_signals = sorted(
            [r for r in rows if r[10] >= 70],
            key=lambda x: x[10],
            reverse=True
        )[:10]

        dashboard_content.extend(top_signals)

        if not top_signals:
            dashboard_content.append(["No high-confidence signals at the moment"])
    else:
        dashboard_content.append(["No Vietnam stock data available"])

    write_table(ws, dashboard_content)
    print(f"✅ Dashboard_Stock_VN updated: {len(rows)} signals from {len(symbol_signals) if rows else 0} unique symbols")
