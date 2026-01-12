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
        "volume": ind.get("volume"),
        "EMA20": ind.get("EMA20"),
        "EMA89": ind.get("EMA89"),
        "EMA200": ind.get("EMA200"),
        "RECOMMENDATION": a.summary.get("RECOMMENDATION"),
    }

def fetch_1d_4h(symbol: str, exchange: str, screener: str) -> dict:
    return {
        "1D": _fetch(symbol, exchange, screener, Interval.INTERVAL_1_DAY),
        "4H": _fetch(symbol, exchange, screener, Interval.INTERVAL_4_HOURS),
    }
