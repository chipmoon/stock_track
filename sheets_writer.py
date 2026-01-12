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

def append_rows(ws, rows):
    if rows:
        ws.append_rows(rows, value_input_option="USER_ENTERED")
