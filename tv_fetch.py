# tv_fetch.py
from tradingview_ta import TA_Handler, Interval

def _fetch(symbol: str, exchange: str, screener: str, interval: Interval) -> dict:
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

def fetch_multi_timeframes(symbol: str, exchange: str, screener: str, timeframes: list) -> dict:
    """
    Fetch data for multiple timeframes
    timeframes: ["4H", "1D", "3D", "1W", "1M"]
    """
    interval_map = {
        "4H": Interval.INTERVAL_4_HOURS,
        "1D": Interval.INTERVAL_1_DAY,
        "3D": Interval.INTERVAL_3_DAYS,
        "1W": Interval.INTERVAL_1_WEEK,
        "1M": Interval.INTERVAL_1_MONTH,
    }
    
    result = {}
    for tf in timeframes:
        if tf in interval_map:
            try:
                result[tf] = _fetch(symbol, exchange, screener, interval_map[tf])
            except Exception as e:
                print(f"⚠️ Error fetching {symbol} {tf}: {e}")
                result[tf] = {}
        else:
            print(f"⚠️ Unknown timeframe: {tf}")
            result[tf] = {}
    
    return result
