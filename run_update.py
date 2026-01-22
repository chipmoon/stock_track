# run_update.py
import os
from datetime import datetime, timezone, timedelta
from config import (
    CRYPTO_TIMEFRAMES, STOCK_TIMEFRAMES,
    TAB_CONFIG, TAB_CRYPTO, TAB_STOCK_TW, TAB_STOCK_VN, TAB_HISTORY,
    TAB_DASHBOARD_STOCK_TW, TAB_DASHBOARD_STOCK_VN, TAB_DASHBOARD_CRYPTO,
    load_config_from_sheet, ensure_config_tab
)
from tv_fetch import fetch_multi_timeframes
from sheets_writer import (
    open_spreadsheet, ensure_tab, write_table, 
    append_rows, update_dashboard_crypto, 
    update_dashboard_stock_tw, update_dashboard_stock_vn,
    delete_tab_if_exists
)

def normalize_value(value):
    """Normalize value to clean string"""
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        return value
    return str(value).strip().upper()


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

    signal_text = "⏸️ WAIT"
    confidence = 0

    if (trend == "BULL" and trend_quality == "STRONG" and momentum == "BULLISH" 
        and volume_strength in ["STRONG", "NORMAL"] and rsi and rsi < 65):
        signal_text = "🚀 STRONG BUY"
        confidence = 90
    elif (trend == "BULL" and rsi and rsi < 35 and close and ema20 and close < ema20):
        signal_text = "📉 DIP BUY"
        confidence = 75
    elif (rsi and rsi < 30 and close and s1 and close <= s1 * 1.02):
        signal_text = "💎 EXTREME VALUE"
        confidence = 85
    elif (trend == "BULL" and close and ema20 and close > ema20):
        signal_text = "✅ HOLD"
        confidence = 60
    elif (trend == "BEAR" and trend_quality == "STRONG" and momentum == "BEARISH"):
        signal_text = "🔴 STRONG SELL"
        confidence = 90
    elif (rsi and rsi > 70 and close and r1 and close >= r1 * 0.98):
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


def process_symbols(symbols, timeframes, asset_type):
    """Process symbols and return data rows"""
    rows = []

    for item in symbols:
        sym = item[0]
        name = item[1]
        exchange = item[2]
        screener = item[3]

        try:
            print(f"🔄 Fetching {asset_type}: {sym} ({exchange}/{screener})...")

            data = fetch_multi_timeframes(sym, exchange, screener, timeframes)

            if not data:
                print(f"❌ No data returned for {sym}")
                rows.append([
                    normalize_value(sym), name, "ERROR", 0, 0, 0,
                    "N/A", "N/A", "N/A", "NO DATA", 0, 0, 0, 0, 0, 0
                ])
                continue

            for tf in timeframes:
                if tf not in data or not data[tf]:
                    print(f"⚠️ Skipping {sym} {tf} - no data")
                    continue

                d = data[tf]
                c = d.get("close")

                if not c:
                    print(f"⚠️ Skipping {sym} {tf} - no close price")
                    continue

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

                clean_symbol = normalize_value(sym.split(":")[-1])
                timeframe = normalize_value(tf)

                row = [
                    clean_symbol,
                    name,
                    timeframe,
                    c,
                    result["rsi"],
                    result["adx"],
                    normalize_value(result["volume_strength"]),
                    normalize_value(result["trend"]),
                    normalize_value(result["trend_quality"]),
                    result["signal"],
                    result["confidence"],
                    e20, e200, pivot, s1, r1
                ]
                rows.append(row)

            print(f"✅ {asset_type}: {clean_symbol} - {len([tf for tf in timeframes if tf in data and data[tf]])} timeframes OK")

        except Exception as e:
            print(f"❌ Critical error {asset_type} {sym}: {e}")
            import traceback
            traceback.print_exc()
            rows.append([
                normalize_value(sym), name, "ERROR", 0, 0, 0,
                "N/A", "N/A", "N/A", f"ERROR: {str(e)[:30]}", 0, 0, 0, 0, 0, 0
            ])

    return rows


def reorder_tabs(ss):
    """
    Reorder tabs in the desired sequence:
    config => history => Crypto => Stock_TW => Stock_VN => Dashboard_Crypto => Dashboard_Stock_TW => Dashboard_Stock_VN
    """
    desired_order = [
        TAB_CONFIG,
        TAB_HISTORY,
        TAB_CRYPTO,
        TAB_STOCK_TW,
        TAB_STOCK_VN,
        TAB_DASHBOARD_CRYPTO,
        TAB_DASHBOARD_STOCK_TW,
        TAB_DASHBOARD_STOCK_VN
    ]

    print("\n📑 Reordering tabs...")
    worksheets = ss.worksheets()

    # Create a mapping of tab names to worksheet objects
    ws_map = {ws.title: ws for ws in worksheets}

    # Reorder tabs
    for index, tab_name in enumerate(desired_order):
        if tab_name in ws_map:
            try:
                ws_map[tab_name].update_index(index)
                print(f"   ✅ {tab_name} → position {index + 1}")
            except Exception as e:
                print(f"   ⚠️ Could not reorder {tab_name}: {e}")


def main():
    sheet_id = os.environ.get("SHEET_ID")
    if not sheet_id:
        raise RuntimeError("Missing SHEET_ID environment variable")

    now_tw = datetime.now(timezone.utc) + timedelta(hours=8)
    ts = now_tw.strftime("%Y-%m-%d %H:%M")

    sa_path = "service_account.json"

    print("🔐 Connecting to Google Sheets...")
    ss = open_spreadsheet(sa_path, sheet_id)

    # === STEP 1: ENSURE CONFIG TAB EXISTS ===
    ensure_config_tab(ss)

    # === STEP 2: LOAD CONFIG FROM GOOGLE SHEET ===
    load_config_from_sheet(ss)

    # Import after loading
    from config import CRYPTO_COINS, STOCK_COINS_TW, STOCK_COINS_VN, FOREX_METALS

    # === STEP 3: DELETE OLD TABS ===
    print("\n🗑️ Removing old tabs...")
    delete_tab_if_exists(ss, "latest")
    delete_tab_if_exists(ss, "Dashboard")
    delete_tab_if_exists(ss, "Stock")  # Old combined stock tab
    delete_tab_if_exists(ss, "Dashboard_Stock")  # Old combined dashboard

    # Header for all tabs
    header = [
        "Symbol", "Name", "TF",
        "Price", "RSI", "ADX", "Vol.Strength",
        "Trend", "Quality", "Buffett Signal", "Confidence%",
        "EMA20", "EMA200", "Pivot", "S1", "R1"
    ]

    # === PROCESS DATA (but don't write yet) ===

    # Crypto
    print(f"\n🚀 Processing Crypto & Forex/Metals...")
    all_crypto_assets = CRYPTO_COINS + FOREX_METALS
    print(f"   - Crypto: {len(CRYPTO_COINS)} symbols")
    print(f"   - Forex/Metals: {len(FOREX_METALS)} symbols")
    crypto_rows = process_symbols(all_crypto_assets, CRYPTO_TIMEFRAMES, "CRYPTO/FOREX")

    # Taiwan stocks
    print(f"\n🇹🇼 Processing {len(STOCK_COINS_TW)} Taiwan stocks...")
    stock_tw_rows = process_symbols(STOCK_COINS_TW, STOCK_TIMEFRAMES, "STOCK_TW")

    # Vietnam stocks
    print(f"\n🇻🇳 Processing {len(STOCK_COINS_VN)} Vietnam stocks...")
    stock_vn_rows = process_symbols(STOCK_COINS_VN, STOCK_TIMEFRAMES, "STOCK_VN")

    # === WRITE DATA IN ORDER ===

    # 1. Config tab (already exists)

    # 2. History tab
    history_header = ["Time(TW)", "Asset Type"] + header
    history_rows = []

    for row in crypto_rows:
        if row[2] != "ERROR":
            history_rows.append([ts, "CRYPTO"] + row)
    for row in stock_tw_rows:
        if row[2] != "ERROR":
            history_rows.append([ts, "STOCK_TW"] + row)
    for row in stock_vn_rows:
        if row[2] != "ERROR":
            history_rows.append([ts, "STOCK_VN"] + row)

    ws_history = ensure_tab(ss, TAB_HISTORY)
    if len(ws_history.get_all_values()) == 0:
        ws_history.update("A1", [history_header])
    if history_rows:
        append_rows(ws_history, history_rows)

    # 3. Crypto tab
    crypto_data = [header] + crypto_rows
    ws_crypto = ensure_tab(ss, TAB_CRYPTO)
    write_table(ws_crypto, crypto_data)

    # 4. Stock_TW tab
    stock_tw_data = [header] + stock_tw_rows
    ws_stock_tw = ensure_tab(ss, TAB_STOCK_TW)
    write_table(ws_stock_tw, stock_tw_data)

    # 5. Stock_VN tab
    stock_vn_data = [header] + stock_vn_rows
    ws_stock_vn = ensure_tab(ss, TAB_STOCK_VN)
    write_table(ws_stock_vn, stock_vn_data)

    # 6-8. Dashboards
    print("\n🎨 Updating Dashboards...")
    update_dashboard_crypto(ss, crypto_data)
    update_dashboard_stock_tw(ss, stock_tw_data)
    update_dashboard_stock_vn(ss, stock_vn_data)

    # === REORDER ALL TABS ===
    reorder_tabs(ss)

    print(f"\n✅ Done! Updated:")
    print(f"   - Crypto: {len([r for r in crypto_rows if r[2] != 'ERROR'])} signals")
    print(f"   - Stock TW: {len([r for r in stock_tw_rows if r[2] != 'ERROR'])} signals")
    print(f"   - Stock VN: {len([r for r in stock_vn_rows if r[2] != 'ERROR'])} signals")
    print(f"   - History: {len(history_rows)} records")
    print(f"\n📑 Tab order: config → history → Crypto → Stock_TW → Stock_VN → Dashboard_Crypto → Dashboard_Stock_TW → Dashboard_Stock_VN")

if __name__ == "__main__":
    main()
