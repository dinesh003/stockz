import pandas as pd
import numpy as np

def calculate_rsi(close_prices: pd.Series, period: int = 14) -> tuple[float, str]:
    """
    Calculates the 14-period RSI using Wilder's smoothing.
    Returns:
    - (latest_rsi: float, rsi_label: str)
    """
    if len(close_prices) <= period:
        return 50.0, "NEUTRAL"
        
    # Calculate price changes
    delta = close_prices.diff()
    
    # Separate gains and losses
    gains = delta.copy()
    losses = delta.copy()
    gains[gains < 0] = 0.0
    losses[losses > 0] = 0.0
    losses = abs(losses)
    
    # Exponential moving averages with alpha = 1 / period (Wilder's smoothing)
    avg_gain = gains.ewm(alpha=1.0 / period, adjust=False).mean()
    avg_loss = losses.ewm(alpha=1.0 / period, adjust=False).mean()
    
    rs = avg_gain / (avg_loss + 1e-10)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    
    latest_rsi = float(rsi.iloc[-1])
    
    if np.isnan(latest_rsi):
        latest_rsi = 50.0
        
    # Labeling
    if latest_rsi >= 60.0:
        label = "BULLISH"
    elif latest_rsi <= 40.0:
        label = "BEARISH"
    else:
        label = "NEUTRAL"
        
    return round(latest_rsi, 2), label
