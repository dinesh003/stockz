import pandas as pd
import numpy as np

def calculate_swings(df: pd.DataFrame, window: int = 20) -> tuple[float, float, float]:
    """
    Calculates recent swing high and swing low from intraday candles.
    Returns:
    - (recent_swing_high: float, recent_swing_low: float, fallback_stop_reference: float)
    """
    if df.empty or 'High' not in df.columns or 'Low' not in df.columns:
        return 0.0, 0.0, 0.0
        
    # Take the tail of the data representing recent sessions
    recent_data = df.tail(100) # last 100 bars (approx 1-2 days of 5m bars)
    
    # Calculate highest high and lowest low in a rolling window of recent bars
    high_series = recent_data['High']
    low_series = recent_data['Low']
    
    # Recent absolute swing points
    swing_high = float(high_series.tail(window).max())
    swing_low = float(low_series.tail(window).min())
    
    # Fallback stop reference (e.g., lowest low/highest high of a wider window)
    wider_window = min(len(recent_data), window * 2)
    fallback_low = float(low_series.tail(wider_window).min())
    fallback_high = float(high_series.tail(wider_window).max())
    
    # If the setup is LONG, the stop fallback is the lower low.
    # If SHORT, it's the higher high. We can return the midpoint or the lower low as a general reference.
    fallback_stop = fallback_low  # default to lowest low
    
    if np.isnan(swing_high):
        swing_high = 0.0
    if np.isnan(swing_low):
        swing_low = 0.0
    if np.isnan(fallback_stop):
        fallback_stop = 0.0
        
    return round(swing_high, 2), round(swing_low, 2), round(fallback_stop, 2)
