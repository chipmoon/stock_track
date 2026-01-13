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

def ensure_tab(spreadsheet, title: str, rows=100, cols=20):
    try:
        ws = spreadsheet.worksheet(title)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=title, rows=str(rows), cols=str(cols))
    return ws

def write_table(ws, values):
    ws.clear()
    ws.update("A1", values)
    
    # Format header đậm + màu nền xám nhẹ
    if len(values) > 0:
        fmt_range = f"A1:{chr(64+len(values[0]))}1"
        ws.format(fmt_range, {
            "textFormat": {"bold": True},
            "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}
        })

def append_rows(ws, rows):
    if rows:
        ws.append_rows(rows, value_input_option="USER_ENTERED")

def update_dashboard_visuals(ss, latest_data):
    """
    Tự động tạo Dashboard với KPI và Chart
    """
    try:
        dash_ws = ss.worksheet("Dashboard")
        ss.del_worksheet(dash_ws)  # Xóa cũ để vẽ lại cho sạch (tránh chart chồng chart)
    except:
        pass
    
    dash_ws = ss.add_worksheet(title="Dashboard", rows="50", cols="20")
    
    # 1. Tính toán KPI từ data
    # Giả sử col index: 5=Trend (BULL/BEAR)
    # Dữ liệu từ run_update.py: [Time, Sym, TF, Price, RSI, Trend, Status...]
    # Index trong code python: Trend là index 5 (cột F)
    
    bull_count = 0
    bear_count = 0
    total = 0
    
    # Bỏ dòng header (row 0)
    for row in latest_data[1:]:
        trend = row[5] # Cột Trend
        if "BULL" in trend: bull_count += 1
        elif "BEAR" in trend: bear_count += 1
        total += 1
        
    # 2. Ghi KPI ra Sheet Dashboard
    dash_ws.update("A1", [
        ["MARKET SENTIMENT OVERVIEW"],
        ["Total Signals", total],
        ["BULLISH 🚀", bull_count],
        ["BEARISH 🐻", bear_count],
        ["NEUTRAL ➖", total - bull_count - bear_count]
    ])
    
    # Format KPI cho đẹp (Màu mè chút)
    dash_ws.format("A1", {"textFormat": {"bold": True, "fontSize": 14}})
    dash_ws.format("A3", {"textFormat": {"foregroundColor": {"red": 0.0, "green": 0.6, "blue": 0.0}, "bold": True}}) # Xanh
    dash_ws.format("A4", {"textFormat": {"foregroundColor": {"red": 0.8, "green": 0.0, "blue": 0.0}, "bold": True}}) # Đỏ

    # 3. Tạo Pie Chart bằng API (BULL vs BEAR vs NEUTRAL)
    # Chart sẽ lấy dữ liệu từ A3:B5 vừa ghi
    sheet_id = dash_ws.id
    
    requests = []
    
    # Pie Chart Request
    requests.append({
        "addChart": {
            "chart": {
                "spec": {
                    "title": "Market Trend Distribution",
                    "pieChart": {
                        "legendPosition": "RIGHT_LEGEND",
                        "domain": {
                            "sourceRange": {
                                "sources": [{
                                    "sheetId": sheet_id,
                                    "startRowIndex": 2, "endRowIndex": 5, # A3:A5 (Label)
                                    "startColumnIndex": 0, "endColumnIndex": 1
                                }]
                            }
                        },
                        "series": {
                            "sourceRange": {
                                "sources": [{
                                    "sheetId": sheet_id,
                                    "startRowIndex": 2, "endRowIndex": 5, # B3:B5 (Value)
                                    "startColumnIndex": 1, "endColumnIndex": 2
                                }]
                            }
                        },
                        "threeDimensional": True # 3D cho đẹp
                    }
                },
                "position": { # Vị trí đặt Chart
                    "overlayPosition": {
                        "anchorCell": {"sheetId": sheet_id, "rowIndex": 0, "columnIndex": 3}, # Bắt đầu ở ô D1
                        "widthPixels": 400,
                        "heightPixels": 300
                    }
                }
            }
        }
    })
    
    # Gửi lệnh tạo chart
    ss.batch_update({"requests": requests})
