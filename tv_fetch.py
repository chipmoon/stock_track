# tv_fetch.py
from tradingview_ta import TA_Handler, Interval

def _fetch(symbol: str, exchange: str, screener: str, interval: Interval) -> dict:
    """Fetch single timeframe data with error handling"""
    try:
        h = TA_Handler(
            symbol=symbol,
            exchange=exchange,
            screener=screener,
            interval=interval,
        )
        a = h.get_analysis()
        ind = a.indicators

        return {
            "open": ind.get("open"),
            "close": ind.get("close"),
            "high": ind.get("high"),
            "low": ind.get("low"),
            "volume": ind.get("volume"),
            "EMA20": ind.get("EMA20"),
            "EMA89": ind.get("EMA89"),
            "EMA200": ind.get("EMA200"),
            "RSI": ind.get("RSI"),
            "MACD": ind.get("MACD.macd"),
            "Signal": ind.get("MACD.signal"),
            "volume_MA": ind.get("volume_MA"),
            "ADX": ind.get("ADX"),
            "ADX+DI": ind.get("ADX+DI"),
            "ADX-DI": ind.get("ADX-DI"),
            "Pivot.M.Classic.Middle": ind.get("Pivot.M.Classic.Middle"),
            "Pivot.M.Classic.S1": ind.get("Pivot.M.Classic.S1"),
            "Pivot.M.Classic.R1": ind.get("Pivot.M.Classic.R1"),
            "BB.upper": ind.get("BB.upper"),
            "BB.lower": ind.get("BB.lower"),
            "RECOMMENDATION": a.summary.get("RECOMMENDATION"),
        }
    except Exception as e:
        print(f"❌ Fetch error {symbol} {interval}: {e}")
        return {}


def fetch_multi_timeframes(symbol: str, exchange: str, screener: str, timeframes: list) -> dict:
    """
    Fetch data for multiple timeframes
    Supported: 1M, 5M, 15M, 30M, 1H, 2H, 4H, 1D, 1W, 1M (month)
    """
    # === ONLY USE SUPPORTED INTERVALS ===
    interval_map = {
        "1M": Interval.INTERVAL_1_MINUTE,
        "5M": Interval.INTERVAL_5_MINUTES,
        "15M": Interval.INTERVAL_15_MINUTES,
        "30M": Interval.INTERVAL_30_MINUTES,
        "1H": Interval.INTERVAL_1_HOUR,
        "2H": Interval.INTERVAL_2_HOURS,
        "4H": Interval.INTERVAL_4_HOURS,
        "1D": Interval.INTERVAL_1_DAY,
        "1W": Interval.INTERVAL_1_WEEK,
        "1M": Interval.INTERVAL_1_MONTH,  # Note: "1M" can mean 1 minute or 1 month
    }
    
    result = {}
    for tf in timeframes:
        if tf in interval_map:
            data = _fetch(symbol, exchange, screener, interval_map[tf])
            if data:  # Only add if fetch succeeded
                result[tf] = data
            else:
                print(f"⚠️ No data for {symbol} {tf}")
                result[tf] = {}
        else:
            print(f"❌ Unsupported timeframe: {tf} (library doesn't support this)")
            result[tf] = {}
    
    return result
