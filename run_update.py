import os
from datetime import datetime, timezone, timedelta
from config import EXCHANGE, SCREENER, TAB_LATEST, TAB_HISTORY, COINS as DEFAULT_COINS
from tv_fetch import fetch_1d_4h
from sheets_writer import open_spreadsheet, ensure_tab, write_table, append_rows, update_dashboard_visuals

# --- HÀM MỚI: Đọc danh sách coin từ Sheet 'config' ---
def get_coins_from_sheet(ss):
    try:
        ws = ss.worksheet("config")
        # Lấy toàn bộ giá trị, bỏ dòng header đầu tiên
        rows = ws.get_all_values()[1:] 
        
        # Filter: Chỉ lấy dòng có Symbol (Cột A không rỗng)
        # Format trả về: [('BTCUSDT', 'Bitcoin'), ('ETHUSDT', 'Ethereum')...]
        sheet_coins = [(r[0].strip(), r[1].strip() if len(r)>1 else r[0].strip()) for r in rows if r[0].strip()]
        
        if not sheet_coins:
            print("⚠️ Tab 'config' is empty. Using default list.")
            return DEFAULT_COINS
            
        print(f"📋 Loaded {len(sheet_coins)} coins from Sheet 'config'.")
        return sheet_coins
    except Exception as e:
        print(f"⚠️ Could not read 'config' tab ({e}). Using default list.")
        return DEFAULT_COINS

def get_pro_status(tf, close, ema20, ema200, rsi, macd, signal):
    trend = "NEUTRAL"
    if close and ema200:
        if close > ema200: trend = "BULL"
        elif close < ema200: trend = "BEAR"
    
    momentum = "WEAK"
    if macd is not None and signal is not None:
        momentum = "UP" if macd > signal else "DOWN"

    status = "WAIT"
    note = ""

    if trend == "BULL":
        if close and ema20 and close > ema20 and momentum == "UP": status = "🚀 STRONG BUY"
        elif close and ema20 and close < ema20: status = "📉 DIP BUY"
        else: status = "✅ HOLD"
    elif trend == "BEAR":
        if momentum == "DOWN": status = "DD STRONG SELL"
        else: status = "⚠️ REVERSAL RISK"

    if rsi and rsi > 70: note = " (Overbought🔥)"
    if rsi and rsi < 30: note = " (Oversold💎)"

    return f"{status}{note}", trend, round(rsi, 1) if rsi else 0

def main():
    sheet_id = os.environ.get("SHEET_ID")
    if not sheet_id: raise RuntimeError("Missing SHEET_ID")

    now_tw = datetime.now(timezone.utc) + timedelta(hours=8)
    ts = now_tw.strftime("%Y-%m-%d %H:%M")

    sa_path = "service_account.json"
    ss = open_spreadsheet(sa_path, sheet_id)
    
    # === LẤY DANH SÁCH COIN ĐỘNG ===
    current_coins = get_coins_from_sheet(ss)

    latest = [[
        "Time(TW)", "Symbol", "TF", 
        "Price", "RSI", "Trend", "Pro Status", 
        "EMA20", "EMA200", "MACD_Hist"
    ]]
    history_rows = []

    print(f"🚀 Fetching data for {len(current_coins)} coins...")

    for sym, name in current_coins:
        try:
            # Tự động thêm 'BINANCE:' nếu user quên nhập trong Sheet
            # tradingview-ta cần format "EXCHANGE:SYMBOL" nếu không dùng hàm search
            # Ở đây ta giả định dùng EXCHANGE từ config (BINANCE)
            
            # Fix: nếu user nhập "BINANCE:BTCUSDT" thì giữ nguyên, nếu nhập "BTCUSDT" thì ghép
            clean_sym = sym.replace("BINANCE:", "") 
            
            data = fetch_1d_4h(clean_sym, EXCHANGE, SCREENER)
            
            for tf in ("1D", "4H"):
                d = data[tf]
                c = d.get("close")
                e20 = d.get("EMA20")
                e200 = d.get("EMA200")
                rsi = d.get("RSI")
                macd = d.get("MACD")
                sig = d.get("Signal")
                
                status_str, trend, rsi_val = get_pro_status(tf, c, e20, e200, rsi, macd, sig)
                macd_hist = round(macd - sig, 2) if (macd and sig) else 0

                row = [ts, sym, tf, c, rsi_val, trend, status_str, e20, e200, macd_hist]
                latest.append(row)
                history_rows.append(row)
                
        except Exception as e:
            print(f"❌ Error fetching {sym}: {e}")
            latest.append([ts, sym, "ERROR", str(e)])

    ws_latest = ensure_tab(ss, TAB_LATEST)
    ws_history = ensure_tab(ss, TAB_HISTORY)

    write_table(ws_latest, latest)
    append_rows(ws_history, history_rows)
    
    print("🎨 Updating Dashboard visuals...")
    update_dashboard_visuals(ss, latest)
    print("✅ Done!")

if __name__ == "__main__":
    main()
