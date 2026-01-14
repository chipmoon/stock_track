# run_update.py
import os
from datetime import datetime, timezone, timedelta
from config import COINS as DEFAULT_COINS, TAB_LATEST, TAB_HISTORY
from tv_fetch import fetch_1d_4h
from sheets_writer import open_spreadsheet, ensure_tab, write_table, append_rows, update_dashboard_visuals

def get_coins_from_sheet(ss):
    """Đọc danh sách coin từ Sheet 'config'"""
    try:
        ws = ss.worksheet("config")
        rows = ws.get_all_values()[1:]
        
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
            print("⚠️ Tab 'config' is empty. Using default list.")
            return DEFAULT_COINS
    except Exception as e:
        print(f"⚠️ Could not read 'config' tab ({e}). Using default list.")
        return DEFAULT_COINS


def get_buffett_signal(close, ema20, ema200, rsi, macd, signal, adx, volume, volume_ma, bb_upper, bb_lower, pivot, s1, r1):
    """Warren Buffett Style Logic"""
    
    trend = "NEUTRAL"
    trend_quality = "WEAK"
    
    if adx:
        if adx > 25:
            trend_quality = "STRONG"
        elif adx > 20:
            trend_quality = "MODERATE"
    
    if close and ema200:
        if close > ema200:
            trend = "BULL"
        elif close < ema200:
            trend = "BEAR"
    
    momentum = "NEUTRAL"
    if macd is not None and signal is not None:
        momentum = "BULLISH" if macd > signal else "BEARISH"
    
    volume_strength = "WEAK"
    if volume and volume_ma:
        if volume > volume_ma * 1.2:
            volume_strength = "STRONG"
        elif volume > volume_ma:
            volume_strength = "NORMAL"
    
    rsi_zone = "NEUTRAL"
    if rsi:
        if rsi < 30:
            rsi_zone = "OVERSOLD"
        elif rsi > 70:
            rsi_zone = "OVERBOUGHT"
    
    signal_text = "⏸️ WAIT"
    confidence = 0
    
    if (trend == "BULL" and trend_quality == "STRONG" and momentum == "BULLISH" 
        and volume_strength in ["STRONG", "NORMAL"] and rsi and rsi < 65):
        signal_text = "🚀 STRONG BUY"
        confidence = 90
    elif (trend == "BULL" and rsi and rsi < 35 and close and ema20 and close < ema20):
        signal_text = "📉 DIP BUY"
        confidence = 75
    elif (rsi_zone == "OVERSOLD" and close and s1 and close <= s1 * 1.02):
        signal_text = "💎 EXTREME VALUE"
        confidence = 85
    elif (trend == "BULL" and close and ema20 and close > ema20):
        signal_text = "✅ HOLD"
        confidence = 60
    elif (trend == "BEAR" and trend_quality == "STRONG" and momentum == "BEARISH"):
        signal_text = "🔴 STRONG SELL"
        confidence = 90
    elif (rsi_zone == "OVERBOUGHT" and close and r1 and close >= r1 * 0.98):
        signal_text = "⚠️ EXIT ZONE"
        confidence = 70
    elif (trend == "BEAR" and momentum == "BULLISH" and adx and adx < 20):
        signal_text = "🔄 REVERSAL WATCH"
        confidence = 50
    elif trend_quality == "WEAK":
        signal_text = "😴 SIDEWAY"
        confidence = 0
    
    return {
        "signal": signal_text,
        "trend": trend,
        "trend_quality": trend_quality,
        "rsi": round(rsi, 1) if rsi else 0,
        "adx": round(adx, 1) if adx else 0,
        "volume_strength": volume_strength,
        "confidence": confidence
    }


def normalize_value(value):
    """
    Chuẩn hóa giá trị thành string sạch (loại bỏ spaces, force uppercase cho text)
    Đảm bảo filter Google Sheets hoạt động 100%
    """
    if value is None:
        return ""
    
    # Nếu là số, giữ nguyên
    if isinstance(value, (int, float)):
        return value
    
    # Nếu là string, clean và uppercase
    return str(value).strip().upper()


def main():
    sheet_id = os.environ.get("SHEET_ID")
    if not sheet_id: 
        raise RuntimeError("Missing SHEET_ID environment variable")

    now_tw = datetime.now(timezone.utc) + timedelta(hours=8)
    ts = now_tw.strftime("%Y-%m-%d %H:%M")

    sa_path = "service_account.json"
    
    print("🔐 Connecting to Google Sheets...")
    ss = open_spreadsheet(sa_path, sheet_id)
    
    current_coins = get_coins_from_sheet(ss)

    latest = [[
        "Time(TW)", "Symbol", "TF", 
        "Price", "RSI", "ADX", "Vol.Strength",
        "Trend", "Quality", "Buffett Signal", "Confidence%",
        "EMA20", "EMA200", "Pivot", "S1", "R1"
    ]]
    history_rows = []

    print(f"🚀 Fetching data for {len(current_coins)} symbols...")

    for item in current_coins:
        try:
            sym = item[0]
            name = item[1] if len(item) > 1 else sym
            exchange = item[2] if len(item) > 2 else "BINANCE"
            screener = item[3] if len(item) > 3 else "crypto"

            # Auto-detect Forex/Gold
            if any(x in sym.upper() for x in ["XAU", "XAG", "EURUSD", "GBPUSD", "USDJPY"]):
                if exchange == "BINANCE": 
                    exchange = "OANDA"
                if screener == "crypto": 
                    screener = "cfd"

            data = fetch_1d_4h(sym, exchange, screener)
            
            for tf in ("1D", "4H"):
                d = data[tf]
                c = d.get("close")
                e20 = d.get("EMA20")
                e200 = d.get("EMA200")
                rsi = d.get("RSI")
                macd = d.get("MACD")
                sig = d.get("Signal")
                adx = d.get("ADX")
                vol = d.get("volume")
                vol_ma = d.get("volume_MA")
                bb_u = d.get("BB.upper")
                bb_l = d.get("BB.lower")
                pivot = d.get("Pivot.M.Classic.Middle")
                s1 = d.get("Pivot.M.Classic.S1")
                r1 = d.get("Pivot.M.Classic.R1")
                
                result = get_buffett_signal(c, e20, e200, rsi, macd, sig, adx, vol, vol_ma, bb_u, bb_l, pivot, s1, r1)

                # === BEST METHOD: Normalize mọi giá trị text ===
                clean_symbol = normalize_value(sym.split(":")[-1])  # "BTCUSDT" not "BINANCE:BTCUSDT"
                timeframe = normalize_value(tf)                      # "1D" or "4H" - guaranteed clean
                
                row = [
                    ts,                                    # Time (keep as-is)
                    clean_symbol,                          # Symbol (cleaned)
                    timeframe,                             # TF (normalized to "1D" or "4H")
                    c,                                     # Price (number)
                    result["rsi"],                         # RSI (number)
                    result["adx"],                         # ADX (number)
                    normalize_value(result["volume_strength"]),  # Vol.Strength (text)
                    normalize_value(result["trend"]),            # Trend (text)
                    normalize_value(result["trend_quality"]),    # Quality (text)
                    result["signal"],                            # Signal (keep emoji)
                    result["confidence"],                        # Confidence (number)
                    e20,                                   # EMA20 (number)
                    e200,                                  # EMA200 (number)
                    pivot,                                 # Pivot (number)
                    s1,                                    # S1 (number)
                    r1                                     # R1 (number)
                ]
                latest.append(row)
                history_rows.append(row)
                
            print(f"✅ {clean_symbol} ({exchange}/{screener})")
                
        except Exception as e:
            print(f"❌ Error fetching {sym}: {e}")
            # Error row với chuẩn hóa
            latest.append([
                ts, 
                normalize_value(sym), 
                "ERROR", 
                0, 0, 0, 
                "N/A", "N/A", "N/A", 
                "ERROR", 
                0, 0, 0, 0, 0, 0
            ])

    print("📝 Writing to Google Sheets...")
    ws_latest = ensure_tab(ss, TAB_LATEST)
    ws_history = ensure_tab(ss, TAB_HISTORY)

    write_table(ws_latest, latest)
    append_rows(ws_history, history_rows)
    
    # === EXTRA SAFETY: Force clean TF column ===
    print("🔧 Ensuring TF column is filter-ready...")
    try:
        # Lấy toàn bộ cột TF (C)
        tf_values = ws_latest.col_values(3)
        
        # Rebuild: strip spaces, force uppercase
        cleaned_tf = []
        for i, val in enumerate(tf_values):
            if i == 0:  # Header
                cleaned_tf.append(["TF"])
            else:
                clean_val = str(val).strip().upper() if val else ""
                cleaned_tf.append([clean_val])
        
        # Ghi đè cột C
        ws_latest.update("C1", cleaned_tf, value_input_option="USER_ENTERED")
        print("✅ TF column cleaned and standardized")
    except Exception as e:
        print(f"⚠️ TF cleanup warning (non-critical): {e}")
    
    print("🎨 Updating Dashboard...")
    update_dashboard_visuals(ss, latest)
    print("✅ Done! Pro Trader Dashboard updated successfully.")

if __name__ == "__main__":
    main()
