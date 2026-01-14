# sheets_writer.py
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

def open_spreadsheet(service_account_json_path: str, sheet_id: str):
    creds = Credentials.from_service_account_file(service_account_json_path, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(sheet_id)

def ensure_tab(spreadsheet, title: str, rows=2000, cols=30):
    try:
        ws = spreadsheet.worksheet(title)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=title, rows=str(rows), cols=str(cols))
    return ws

def write_table(ws, values):
    ws.clear()
    ws.update("A1", values)
    
    # Format header (bold + gray background)
    if len(values) > 0 and len(values[0]) > 0:
        fmt_range = f"A1:{chr(64 + min(len(values[0]), 26))}1"
        ws.format(fmt_range, {
            "textFormat": {"bold": True},
            "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}
        })

def append_rows(ws, rows):
    if rows:
        ws.append_rows(rows, value_input_option="USER_ENTERED")

def update_dashboard_visuals(ss, latest_data):
    """
    Tự động tạo Dashboard với KPI và Pie Chart
    Cấu trúc cột mới: Time(TW) | Symbol | TF | Price | RSI | ADX | Vol.Strength | Trend | Quality | Buffett Signal | Confidence% | ...
    Index:            0         1        2    3       4     5     6              7       8         9                10
    """
    try:
        dash_ws = ss.worksheet("Dashboard")
        ss.del_worksheet(dash_ws)
    except:
        pass
    
    dash_ws = ss.add_worksheet(title="Dashboard", rows="50", cols="20")
    
    # Tính toán KPI từ data (Trend ở index 7, Buffett Signal ở index 9)
    bull_count = 0
    bear_count = 0
    neutral_count = 0
    strong_buy_count = 0
    total = 0
    
    for row in latest_data[1:]:  # Bỏ header
        if len(row) < 10:  # Bỏ qua dòng lỗi
            continue
            
        # Lấy cột Trend (index 7) và Signal (index 9)
        trend = str(row[7]) if row[7] else "NEUTRAL"
        signal = str(row[9]) if row[9] else "WAIT"
        
        # Đếm Trend
        if "BULL" in trend.upper():
            bull_count += 1
        elif "BEAR" in trend.upper():
            bear_count += 1
        else:
            neutral_count += 1
        
        # Đếm Strong Buy signals
        if "STRONG BUY" in signal.upper():
            strong_buy_count += 1
            
        total += 1
    
    # Ghi KPI ra Dashboard
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
    
    # Format cho đẹp
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
    dash_ws.format("A8", {
        "textFormat": {"foregroundColor": {"red": 0.0, "green": 0.5, "blue": 0.8}, "bold": True, "fontSize": 14}
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
                                    "startRowIndex": 3,  # A4 (BULLISH)
                                    "endRowIndex": 6,    # A6 (NEUTRAL)
                                    "startColumnIndex": 0,
                                    "endColumnIndex": 1
                                }]
                            }
                        },
                        "series": {
                            "sourceRange": {
                                "sources": [{
                                    "sheetId": sheet_id,
                                    "startRowIndex": 3,  # B4
                                    "endRowIndex": 6,    # B6
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
                        "anchorCell": {
                            "sheetId": sheet_id, 
                            "rowIndex": 0, 
                            "columnIndex": 3
                        },
                        "widthPixels": 450,
                        "heightPixels": 300
                    }
                }
            }
        }
    }]
    
    ss.batch_update({"requests": requests})
    
    print(f"📊 Dashboard: {bull_count} Bull | {bear_count} Bear | {strong_buy_count} Strong Buy signals")
