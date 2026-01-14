# run_update.py
import os
from datetime import datetime, timezone, timedelta
from config import COINS as DEFAULT_COINS, TAB_LATEST, TAB_HISTORY
from tv_fetch import fetch_1d_4h
from sheets_writer import open_spreadsheet, ensure_tab, write_table, append_rows, update_dashboard_visuals

def get_coins_from_sheet(ss):
    """Đọc danh sách coin từ Sheet 'config' (4 cột: Symbol|Name|Exchange|Screener)"""
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
            print("⚠️ Tab 'config' is empty. Using default list.")
            return DEFAULT_COINS
    except Exception as e:
        print(f"⚠️ Could not read 'config' tab ({e}). Using default list.")
        return DEFAULT_COINS


def get_buffett_signal(close, ema20, ema200, rsi, macd, signal, adx, volume, volume_ma, bb_upper, bb_lower, pivot, s1, r1):
    """
    Warren Buffett Style Logic:
    1. Trend Quality (ADX > 25 = Strong, < 20 = Weak)
    2. Value Zone (RSI extreme + Price near support/resistance)
    3. Volume Confirmation (Volume > MA)
    4. Risk Management (BB squeeze, Pivot levels)
    """
    
    # 1. Trend Analysis
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
    
    # 2. Momentum
    momentum = "NEUTRAL"
    if macd is not None and signal is not None:
        if macd > signal:
            momentum = "BULLISH"
        else:
            momentum = "BEARISH"
    
    # 3. Volume Confirmation (Warren: "Volume precedes price")
    volume_strength = "WEAK"
    if volume and volume_ma and volume > volume_ma * 1.2:
        volume_strength = "STRONG"
    elif volume and volume_ma and volume > volume_ma:
        volume_strength = "NORMAL"
    
    # 4. Value Zones (RSI extremes)
    rsi_zone = "NEUTRAL"
    if rsi:
        if rsi < 30:
            rsi_zone = "OVERSOLD 💎"
        elif rsi > 70:
            rsi_zone = "OVERBOUGHT 🔥"
        elif 40 <= rsi <= 60:
            rsi_zone = "BALANCED"
    
    # 5. Ultimate Signal (Confluence Logic)
    signal_text = "⏸️ WAIT"
    confidence = 0
    
    # STRONG BUY Conditions
    if (trend == "BULL" and trend_quality == "STRONG" and momentum == "BULLISH" 
        and volume_strength in ["STRONG", "NORMAL"] and rsi and rsi < 65):
        signal_text = "🚀 STRONG BUY"
        confidence = 90
    
    # DIP BUY (Buffett: "Be greedy when others are fearful")
    elif (trend == "BULL" and rsi and rsi < 35 and close and ema20 and close < ema20):
        signal_text = "📉 DIP BUY (Value)"
        confidence = 75
    
    # OVERSOLD Opportunity (Near support)
    elif (rsi_zone == "OVERSOLD 💎" and close and s1 and close <= s1 * 1.02):
        signal_text = "💎 EXTREME VALUE (Rare)"
        confidence = 85
    
    # HOLD (Trend intact but momentum weak)
    elif (trend == "BULL" and close and ema20 and close > ema20):
        signal_text = "✅ HOLD"
        confidence = 60
    
    # SELL Signals
    elif (trend == "BEAR" and trend_quality == "STRONG" and momentum == "BEARISH"):
        signal_text = "🔴 STRONG SELL"
        confidence = 90
    
    # OVERBOUGHT Warning (Near resistance)
    elif (rsi_zone == "OVERBOUGHT 🔥" and close and r1 and close >= r1 * 0.98):
        signal_text = "⚠️ EXIT ZONE (Take Profit)"
        confidence = 70
    
    # REVERSAL Risk
    elif (trend == "BEAR" and momentum == "BULLISH" and adx and adx < 20):
        signal_text = "🔄 REVERSAL WATCH"
        confidence = 50
    
    # Weak Trend = Sideway
    elif trend_quality == "WEAK":
        signal_text = "😴 SIDEWAY (No Trade)"
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
            if "XAU" in sym.upper() or "XAG" in sym.upper() or "EURUSD" in sym.upper():
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
            
                # CLEAN & STANDARDIZE
                clean_symbol = sym.split(":")[-1].strip()  # Remove exchange prefix
                timeframe = tf.strip().upper()              # Force uppercase
                
                row = [
                    ts, 
                    clean_symbol,      # ← Clean symbol (EURUSD not OANDA:EURUSD)
                    timeframe,         # ← Standard TF (1D not 1d)
                    c, 
                    result["rsi"], 
                    result["adx"],
                    result["volume_strength"],
                    result["trend"], 
                    result["trend_quality"],
                    result["signal"], 
                    result["confidence"],
                    e20, e200, pivot, s1, r1
                ]
                latest.append(row)
                history_rows.append(row)
                
            print(f"✅ {sym} ({exchange}/{screener})")
                
        except Exception as e:
            print(f"❌ Error fetching {sym}: {e}")
            latest.append([ts, sym, "ERROR", str(e), 0, 0, "N/A", "N/A", "N/A", "ERROR", 0, 0, 0, 0, 0, 0])

    ws_latest = ensure_tab(ss, TAB_LATEST)
    ws_history = ensure_tab(ss, TAB_HISTORY)

    write_table(ws_latest, latest)
    append_rows(ws_history, history_rows)
    
    print("🎨 Updating Dashboard visuals...")
    update_dashboard_visuals(ss, latest)
    print("✅ Done! Pro Trader Dashboard updated successfully.")

if __name__ == "__main__":
    main()

