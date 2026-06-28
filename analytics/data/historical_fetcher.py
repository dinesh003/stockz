from data.provider_client import fetch_historical_daily_candles

def get_historical_candles(symbol, lookback_days=60):
    """
    Retrieves historical daily candles for the given symbol.
    Returns a pandas DataFrame.
    """
    return fetch_historical_daily_candles(symbol, lookback_days)
