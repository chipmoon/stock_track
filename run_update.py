# run_update.py
import os
from datetime import datetime, timezone, timedelta

from config import COINS, EXCHANGE, SCREENER, TAB_LATEST, TAB_HISTORY
from tv_fetch import fetch_1d_4h
from sheets_writer import open_spreadsheet, ensure_tab, write_table, append_rows

def ema_stack_score(close, ema20, ema89, ema200) -> int:
    score = 0
    if close is not None and ema200 is not None and close > ema200:
        score += 4
    if ema89 is not None and ema200 is not None and ema89 > ema200:
        score += 3
    if ema20 is not None and ema89 is not None and ema20 > ema89:
        score += 2
    return score  # 0..9

def main():
    print("Debug: All env vars:", list(os.environ.keys())) 
    sheet_id = os.environ.get("SHEET_ID")
    print("Debug: SHEET_ID value:", sheet_id)  
    if not sheet_id:
        raise RuntimeError("Missing SHEET_ID environment variable")

    # Taiwan time (UTC+8)
    now_tw = datetime.now(timezone.utc) + timedelta(hours=8)
    ts = now_tw.strftime("%Y-%m-%d %H:%M")

    latest = [[
        "Time(TW)", "Symbol", "Name", "TF",
        "Open", "Close", "Volume",
        "EMA20", "EMA89", "EMA200",
        "EMA Stack Score(0-9)", "Trend", "TV_Recommendation"
    ]]
    history_rows = []

    for sym, name in COINS:
        data = fetch_1d_4h(sym, EXCHANGE, SCREENER)
        for tf in ("1D", "4H"):
            d = data[tf]
            o = d.get("open")
            c = d.get("close")
            v = d.get("volume")
            e20 = d.get("EMA20")
            e89 = d.get("EMA89")
            e200 = d.get("EMA200")
            rec = d.get("RECOMMENDATION")

            score = ema_stack_score(c, e20, e89, e200)
            trend = "BULL" if (c is not None and e200 is not None and c > e200) else "BEAR/NEUTRAL"

            row = [ts, sym, name, tf, o, c, v, e20, e89, e200, score, trend, rec]
            latest.append(row)
            history_rows.append(row)

    sa_path = "service_account.json"  # created by GitHub Actions step
    ss = open_spreadsheet(sa_path, sheet_id)
    ws_latest = ensure_tab(ss, TAB_LATEST)
    ws_history = ensure_tab(ss, TAB_HISTORY)

    write_table(ws_latest, latest)
    append_rows(ws_history, history_rows)

if __name__ == "__main__":
    main()
