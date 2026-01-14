# sheets_writer.py
import gspread
from google.oauth2.service_account import Credentials
import time

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

def open_spreadsheet(service_account_json_path: str, sheet_id: str, max_retries=3):
    """
    Mở Google Sheet với retry logic để tránh lỗi 503 tạm thời
    """
    creds = Credentials.from_service_account_file(service_account_json_path, scopes=SCOPES)
    client = gspread.authorize(creds)
    
    for attempt in range(max_retries):
        try:
            return client.open_by_key(sheet_id)
        except gspread.exceptions.APIError as e:
            if "503" in str(e) or "429" in str(e):  # Service unavailable or Rate limit
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5  # 5s, 10s, 15s
                    print(f"⚠️ Google Sheets API error: {e}. Retrying in {wait_time}s... (Attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    print(f"❌ Failed after {max_retries} attempts. Google Sheets may be temporarily down.")
                    raise
            else:
                raise  # Other API errors (permission, etc.)
        except Exception as e:
            print(f"❌ Unexpected error opening spreadsheet: {e}")
            raise
    
    raise RuntimeError("Failed to open spreadsheet after retries")

def ensure_tab(spreadsheet, title: str, rows=2000, cols=30):
    try:
        ws = spreadsheet.worksheet(title)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=title, rows=str(rows), cols=str(cols))
    return ws

def write_table(ws, values, max_retries=3):
    """
    Ghi dữ liệu với retry logic
    """
    for attempt in range(max_retries):
        try:
            ws.clear()
            ws.update("A1", values, value_input_option="USER_ENTERED")
            
            # Format header
            if len(values) > 0 and len(values[0]) > 0:
                fmt_range = f"A1:{chr(64 + min(len(values[0]), 26))}1"
                ws.format(fmt_range, {
                    "textFormat": {"bold": True},
                    "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}
                })
            return
        except gspread.exceptions.APIError as e:
            if "503" in str(e) or "429" in str(e):
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 3
                    print(f"⚠️ Write error: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise
            else:
                raise

def append_rows(ws, rows, max_retries=3):
    if not rows:
        return
        
    for attempt in range(max_retries):
        try:
            ws.append_rows(rows, value_input_option="USER_ENTERED")
            return
        except gspread.exceptions.APIError as e:
            if "503" in str(e) or "429" in str(e):
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 3
                    print(f"⚠️ Append error: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise
            else:
                raise

def update_dashboard_visuals(ss, latest_data):
    """
    Tự động tạo Dashboard với KPI và Pie Chart
    """
    try:
        dash_ws = ss.worksheet("Dashboard")
        ss.del_worksheet(dash_ws)
    except:
        pass
    
    dash_ws = ss.add_worksheet(title="Dashboard", rows="50", cols="20")
    
    # Tính toán KPI (Trend ở index 7, Signal ở index 9)
    bull_count = 0
    bear_count = 0
    neutral_count = 0
    strong_buy_count = 0
    total = 0
    
    for row in latest_data[1:]:
        if len(row) < 10:
            continue
            
        trend = str(row[7]).strip().upper() if row[7] else "NEUTRAL"
        signal = str(row[9]).strip().upper() if row[9] else "WAIT"
        
        if "BULL" in trend:
            bull_count += 1
        elif "BEAR" in trend:
            bear_count += 1
        else:
            neutral_count += 1
        
        if "STRONG BUY" in signal:
            strong_buy_count += 1
            
        total += 1
    
    # Ghi KPI
    dash_ws.update("A1", [
        ["📊 WARREN BUFFETT DASHBOARD"],
        [""],
        ["Total Signals", total],
        ["🚀 BULLISH Trend", bull_count],
        ["🔴 BEARISH Trend", bear_count],
        ["😴 NEUTRAL/Sideway", neutral_count],
        [""],
        ["💎 Strong Buy Signals", strong_buy_count],
    ])
    
    # Format
    dash_ws.format("A1", {
        "textFormat": {"bold": True, "fontSize": 16},
        "backgroundColor": {"red": 0.2, "green": 0.3, "blue": 0.5}
    })
    dash_ws.format("A4", {
        "textFormat": {"foregroundColor": {"red": 0.0, "green": 0.7, "blue": 0.0}, "bold": True}
    })
    dash_ws.format("A5", {
        "textFormat": {"foregroundColor": {"red": 0.8, "green": 0.0, "blue": 0.0}, "bold": True}
    })
    
    # Tạo Pie Chart
    sheet_id = dash_ws.id
    
    requests = [{
        "addChart": {
            "chart": {
                "spec": {
                    "title": "Market Sentiment Distribution",
                    "pieChart": {
                        "legendPosition": "RIGHT_LEGEND",
                        "domain": {
                            "sourceRange": {
                                "sources": [{
                                    "sheetId": sheet_id,
                                    "startRowIndex": 3,
                                    "endRowIndex": 6,
                                    "startColumnIndex": 0,
                                    "endColumnIndex": 1
                                }]
                            }
                        },
                        "series": {
                            "sourceRange": {
                                "sources": [{
                                    "sheetId": sheet_id,
                                    "startRowIndex": 3,
                                    "endRowIndex": 6,
                                    "startColumnIndex": 1,
                                    "endColumnIndex": 2
                                }]
                            }
                        },
                        "threeDimensional": True
                    }
                },
                "position": {
                    "overlayPosition": {
                        "anchorCell": {"sheetId": sheet_id, "rowIndex": 0, "columnIndex": 3},
                        "widthPixels": 450,
                        "heightPixels": 300
                    }
                }
            }
        }
    }]
    
    try:
        ss.batch_update({"requests": requests})
        print(f"📊 Dashboard: {bull_count} Bull | {bear_count} Bear | {strong_buy_count} Strong Buy")
    except Exception as e:
        print(f"⚠️ Chart creation skipped (non-critical): {e}")
