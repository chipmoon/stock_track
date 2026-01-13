import os
from datetime import datetime, timezone, timedelta
from config import COINS as DEFAULT_COINS, TAB_LATEST, TAB_HISTORY
from tv_fetch import fetch_1d_4h
from sheets_writer import open_spreadsheet, ensure_tab, write_table, append_rows, update_dashboard_visuals

# --- Đọc danh sách coin từ Sheet 'config' (4 cột: Symbol|Name|Exchange|Screener) ---
def get_coins_from_sheet(ss):
    try:
        ws = ss.worksheet("config")
        rows = ws.get_all_values()[1:]  # Bỏ header
        
        coins = []
        for r in rows:
            if not r[0].strip(): 
                continue
            sym = r[0].strip()
            name = r[1].strip() if len(r) > 1 and r[1].strip() else sym
            exc = r[2].strip() if len(r) > 2 and r[2].strip() else "BINANCE"
            scr = r[3].strip() if len(r) > 3 and r[3].strip() else "crypto"
            coins.append((sym, name, exc, scr))
            
        if coins:
            print(f"📋 Loaded {len(coins)} symbols from Sheet 'config'.")
            return coins
        else:
            print("⚠️ Tab 'config' is empty. Using default list from config.py")
            return DEFAULT_COINS
    except Exception as e:
        print(f"⚠️ Could not read 'config' tab ({e}). Using default list.")
        return DEFAULT_COINS

def get_pro_status(tf, close, ema20, ema200, rsi, macd, signal):
    trend = "NEUTRAL"
    if close and ema200:
        if close > ema200: 
            trend = "BULL"
        elif close < ema200: 
            trend = "BEAR"
    
    momentum = "WEAK"
    if macd is not None and signal is not None:
        momentum = "UP" if macd > signal else "DOWN"

    status = "WAIT"
    note = ""

    if trend == "BULL":
        if close and ema20 and close > ema20 and momentum == "UP": 
            status = "🚀 STRONG BUY"
        elif close and ema20 and close < ema20: 
            status = "📉 DIP BUY"
        else: 
            status = "✅ HOLD"
    elif trend == "BEAR":
        if momentum == "DOWN": 
            status = "🔴 STRONG SELL"
        else: 
            status = "⚠️ REVERSAL RISK"

    if rsi and rsi > 70: 
        note = " (Overbought🔥)"
    if rsi and rsi < 30: 
        note = " (Oversold💎)"

    return f"{status}{note}", trend, round(rsi, 1) if rsi else 0

def main():
    sheet_id = os.environ.get("SHEET_ID")
    if not sheet_id: 
        raise RuntimeError("Missing SHEET_ID environment variable")

    now_tw = datetime.now(timezone.utc) + timedelta(hours=8)
    ts = now_tw.strftime("%Y-%m-%d %H:%M")

    sa_path = "service_account.json"
    ss = open_spreadsheet(sa_path, sheet_id)
    
    # Lấy danh sách coin động từ Sheet config
    current_coins = get_coins_from_sheet(ss)

    latest = [[
        "Time(TW)", "Symbol", "TF", 
        "Price", "RSI", "Trend", "Pro Status", 
        "EMA20", "EMA200", "MACD_Hist"
    ]]
    history_rows = []

    print(f"🚀 Fetching data for {len(current_coins)} symbols...")

    for item in current_coins:
        try:
            # Unpack theo format (sym, name, exchange, screener)
            sym = item[0]
            name = item[1] if len(item) > 1 else sym
            exchange = item[2] if len(item) > 2 else "BINANCE"
            screener = item[3] if len(item) > 3 else "crypto"

            # Auto-detect nếu user quên điền Exchange/Screener
            if "XAU" in sym.upper() or "XAG" in sym.upper() or "EURUSD" in sym.upper():
                if exchange == "BINANCE": 
                    exchange = "OANDA"
                if screener == "crypto": 
                    screener = "cfd"

            # Fetch data cho cả 1D và 4H
            data = fetch_1d_4h(sym, exchange, screener)
            
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
                
            print(f"✅ {sym} ({exchange}/{screener})")
                
        except Exception as e:
            print(f"❌ Error fetching {sym}: {e}")
            latest.append([ts, sym, "ERROR", str(e), 0, "N/A", "ERROR", 0, 0, 0])

    ws_latest = ensure_tab(ss, TAB_LATEST)
    ws_history = ensure_tab(ss, TAB_HISTORY)

    write_table(ws_latest, latest)
    append_rows(ws_history, history_rows)
    
    print("🎨 Updating Dashboard visuals...")
    update_dashboard_visuals(ss, latest)
    print("✅ Done! Dashboard updated successfully.")

if __name__ == "__main__":
    main()
