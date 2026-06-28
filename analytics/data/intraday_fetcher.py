from data.provider_client import fetch_intraday_candles

def get_intraday_candles(symbol, interval="5m", days=5):
    """
    Retrieves intraday candles (e.g. 5-minute interval) for the given symbol.
    Returns a pandas DataFrame.
    """
    return fetch_intraday_candles(symbol, interval, days)
