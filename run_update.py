import os
from datetime import datetime, timezone, timedelta
from config import COINS, EXCHANGE, SCREENER, TAB_LATEST, TAB_HISTORY
from tv_fetch import fetch_1d_4h
from sheets_writer import open_spreadsheet, ensure_tab, write_table, append_rows, update_dashboard_visuals

def get_pro_status(tf, close, ema20, ema200, rsi, macd, signal):
    # 1. Xác định Trend
    trend = "NEUTRAL"
    if close > ema200:
        trend = "BULL"
    elif close < ema200:
        trend = "BEAR"
    
    # 2. Xác định Momentum (MACD)
    momentum = "WEAK"
    if macd > signal:
        momentum = "UP"
    else:
        momentum = "DOWN"

    # 3. Tổng hợp Trạng thái Pro
    status = "WAIT"
    note = ""

    if trend == "BULL":
        if close > ema20 and momentum == "UP":
            status = "🚀 STRONG BUY"
        elif close < ema20:
            status = "📉 DIP BUY (Watch)"  # Giá trên EMA200 nhưng dưới EMA20 -> Mua khi điều chỉnh
        else:
            status = "✅ HOLD"
    elif trend == "BEAR":
        if momentum == "DOWN":
            status = "DD STRONG SELL"
        else:
            status = "⚠️ REVERSAL RISK" # Giá giảm nhưng momentum tăng -> Coi chừng đảo chiều

    # Cảnh báo RSI
    if rsi > 70: note = " (Overbought🔥)"
    if rsi < 30: note = " (Oversold💎)"

    return f"{status}{note}", trend, round(rsi, 1)

def main():
    sheet_id = os.environ.get("SHEET_ID")
    if not sheet_id:
        raise RuntimeError("Missing SHEET_ID environment variable")

    now_tw = datetime.now(timezone.utc) + timedelta(hours=8)
    ts = now_tw.strftime("%Y-%m-%d %H:%M")

    # Header mới chuyên nghiệp hơn
    latest = [[
        "Time(TW)", "Symbol", "TF", 
        "Price", "RSI", "Trend", "Pro Status", 
        "EMA20", "EMA200", "MACD_Hist"
    ]]
    history_rows = []

    for sym, name in COINS:
        data = fetch_1d_4h(sym, EXCHANGE, SCREENER)
        for tf in ("1D", "4H"):
            d = data[tf]
            c = d.get("close")
            e20 = d.get("EMA20")
            e200 = d.get("EMA200")
            rsi = d.get("RSI")
            macd = d.get("MACD")
            sig = d.get("Signal")
            
            # Tính toán logic
            status_str, trend, rsi_val = get_pro_status(tf, c, e20, e200, rsi, macd, sig)
            macd_hist = round(macd - sig, 2) if (macd and sig) else 0

            # Format hàng dữ liệu
            row = [
                ts, sym, tf, 
                c, rsi_val, trend, status_str,
                e20, e200, macd_hist
            ]
            
            latest.append(row)
            history_rows.append(row)

    sa_path = "service_account.json"
    ss = open_spreadsheet(sa_path, sheet_id)
    ws_latest = ensure_tab(ss, TAB_LATEST)
    ws_history = ensure_tab(ss, TAB_HISTORY)

    write_table(ws_latest, latest)
    append_rows(ws_history, history_rows)
    
    # === THÊM DÒNG NÀY ĐỂ VẼ DASHBOARD ===
    print("🎨 Updating Dashboard visuals...")
    update_dashboard_visuals(ss, latest)
    print("✅ Done!")
    
if __name__ == "__main__":
    main()


