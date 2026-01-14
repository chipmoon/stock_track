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
        # Price Action
        "open": ind.get("open"),
        "close": ind.get("close"),
        "high": ind.get("high"),
        "low": ind.get("low"),
        "volume": ind.get("volume"),
        
        # Moving Averages (Trend)
        "EMA20": ind.get("EMA20"),
        "EMA89": ind.get("EMA89"),
        "EMA200": ind.get("EMA200"),
        
        # Momentum Indicators
        "RSI": ind.get("RSI"),
        "MACD": ind.get("MACD.macd"),
        "Signal": ind.get("MACD.signal"),
        
        # Volume Analysis (Warren Buffett Style)
        "volume_MA": ind.get("volume_MA"),
        
        # Trend Strength (Professional Confirmation)
        "ADX": ind.get("ADX"),
        "ADX+DI": ind.get("ADX+DI"),
        "ADX-DI": ind.get("ADX-DI"),
        
        # Support/Resistance
        "Pivot.M.Classic.Middle": ind.get("Pivot.M.Classic.Middle"),
        "Pivot.M.Classic.S1": ind.get("Pivot.M.Classic.S1"),
        "Pivot.M.Classic.R1": ind.get("Pivot.M.Classic.R1"),
        
        # Bollinger Bands (Volatility)
        "BB.upper": ind.get("BB.upper"),
        "BB.lower": ind.get("BB.lower"),
        
        "RECOMMENDATION": a.summary.get("RECOMMENDATION"),
    }

def fetch_1d_4h(symbol: str, exchange: str, screener: str) -> dict:
    return {
        "1D": _fetch(symbol, exchange, screener, Interval.INTERVAL_1_DAY),
        "4H": _fetch(symbol, exchange, screener, Interval.INTERVAL_4_HOURS),
    }
