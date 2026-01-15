# sheets_writer.py
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def open_spreadsheet(sa_json_path: str, sheet_id: str):
    """Connect to Google Sheets"""
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(sa_json_path, scope)
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

    # Extract header and data rows
    header = crypto_data[0] if crypto_data else []
    rows = crypto_data[1:] if len(crypto_data) > 1 else []

    # Build dashboard
    dashboard_content = []
    dashboard_content.append(["📊 CRYPTO DASHBOARD"])
    dashboard_content.append([])

    # Summary statistics
    if rows:
        strong_buy = len([r for r in rows if "STRONG BUY" in str(r[9])])
        dip_buy = len([r for r in rows if "DIP BUY" in str(r[9])])
        hold = len([r for r in rows if "HOLD" in str(r[9])])
        sell = len([r for r in rows if "SELL" in str(r[9])])

        dashboard_content.append(["=== SIGNAL SUMMARY ==="])
        dashboard_content.append(["🚀 Strong Buy:", strong_buy])
        dashboard_content.append(["📉 Dip Buy:", dip_buy])
        dashboard_content.append(["✅ Hold:", hold])
        dashboard_content.append(["🔴 Sell:", sell])
        dashboard_content.append([])

        # Top opportunities (confidence >= 75)
        dashboard_content.append(["=== TOP CRYPTO OPPORTUNITIES ==="])
        dashboard_content.append(header)

        top_signals = sorted(
            [r for r in rows if r[10] >= 75],  # confidence >= 75
            key=lambda x: x[10],  # sort by confidence
            reverse=True
        )[:10]  # top 10

        dashboard_content.extend(top_signals)

        if not top_signals:
            dashboard_content.append(["No high-confidence signals at the moment"])
    else:
        dashboard_content.append(["No crypto data available"])

    write_table(ws, dashboard_content)
    print(f"✅ Dashboard_Crypto updated: {len(rows)} crypto signals")


def update_dashboard_stock(ss, stock_data):
    """
    Update Dashboard_Stock with summary and top signals
    stock_data format: [header, row1, row2, ...]
    """
    from config import TAB_DASHBOARD_STOCK

    ws = ensure_tab(ss, TAB_DASHBOARD_STOCK)
    ws.clear()

    # Extract header and data rows
    header = stock_data[0] if stock_data else []
    rows = stock_data[1:] if len(stock_data) > 1 else []

    # Build dashboard
    dashboard_content = []
    dashboard_content.append(["📈 STOCK DASHBOARD"])
    dashboard_content.append([])

    # Summary statistics
    if rows:
        strong_buy = len([r for r in rows if "STRONG BUY" in str(r[9])])
        dip_buy = len([r for r in rows if "DIP BUY" in str(r[9])])
        extreme_value = len([r for r in rows if "EXTREME VALUE" in str(r[9])])
        hold = len([r for r in rows if "HOLD" in str(r[9])])
        sell = len([r for r in rows if "SELL" in str(r[9])])

        dashboard_content.append(["=== SIGNAL SUMMARY ==="])
        dashboard_content.append(["🚀 Strong Buy:", strong_buy])
        dashboard_content.append(["📉 Dip Buy:", dip_buy])
        dashboard_content.append(["💎 Extreme Value:", extreme_value])
        dashboard_content.append(["✅ Hold:", hold])
        dashboard_content.append(["🔴 Sell:", sell])
        dashboard_content.append([])

        # Top opportunities (confidence >= 70)
        dashboard_content.append(["=== TOP STOCK OPPORTUNITIES ==="])
        dashboard_content.append(header)

        top_signals = sorted(
            [r for r in rows if r[10] >= 70],  # confidence >= 70
            key=lambda x: x[10],  # sort by confidence
            reverse=True
        )[:10]  # top 10

        dashboard_content.extend(top_signals)

        if not top_signals:
            dashboard_content.append(["No high-confidence signals at the moment"])
    else:
        dashboard_content.append(["No stock data available"])

    write_table(ws, dashboard_content)
    print(f"✅ Dashboard_Stock updated: {len(rows)} stock signals")
