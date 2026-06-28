import pandas as pd
import numpy as np

def calculate_bollinger_bands(close_prices: pd.Series, period: int = 20, num_std: float = 2.0) -> tuple[float, float, float, str]:
    """
    Calculates Bollinger Bands and returns:
    - (upper_band, middle_band, lower_band, state)
    
    States:
    - UPPER_BAND_BREAKOUT
    - LOWER_BAND_BREAKDOWN
    - UPPER_BAND_TOUCH
    - LOWER_BAND_TOUCH
    - INSIDE_BANDS
    """
    if len(close_prices) < period:
        # Fallback if insufficient data
        last_price = close_prices.iloc[-1] if not close_prices.empty else 0.0
        return last_price, last_price, last_price, "INSIDE_BANDS"
        
    # Calculate SMA (Middle Band)
    middle_band = close_prices.rolling(window=period).mean()
    
    # Calculate rolling standard deviation
    rolling_std = close_prices.rolling(window=period).std()
    
    # Calculate Upper and Lower bands
    upper_band = middle_band + (num_std * rolling_std)
    lower_band = middle_band - (num_std * rolling_std)
    
    last_close = float(close_prices.iloc[-1])
    last_upper = float(upper_band.iloc[-1])
    last_middle = float(middle_band.iloc[-1])
    last_lower = float(lower_band.iloc[-1])
    
    if np.isnan(last_upper) or np.isnan(last_lower):
        return last_close, last_close, last_close, "INSIDE_BANDS"
        
    # Determine state
    if last_close > last_upper:
        state = "UPPER_BAND_BREAKOUT"
    elif last_close < last_lower:
        state = "LOWER_BAND_BREAKDOWN"
    elif abs(last_close - last_upper) / last_upper <= 0.005:  # within 0.5%
        state = "UPPER_BAND_TOUCH"
    elif abs(last_close - last_lower) / last_lower <= 0.005:  # within 0.5%
        state = "LOWER_BAND_TOUCH"
    else:
        state = "INSIDE_BANDS"
        
    return round(last_upper, 2), round(last_middle, 2), round(last_lower, 2), state
