import pandas as pd
import numpy as np

def calculate_atr(df: pd.DataFrame, period: int = 14) -> float:
    """
    Calculates the 14-period Average True Range (ATR).
    Input DataFrame must have High, Low, and Close columns.
    """
    if len(df) <= period:
        # Fallback to simple range average if data is limited
        if not df.empty and 'High' in df.columns and 'Low' in df.columns:
            tr_fallback = df['High'] - df['Low']
            return float(round(tr_fallback.mean(), 2))
        return 0.0
        
    high = df['High']
    low = df['Low']
    prev_close = df['Close'].shift(1)
    
    # True Range calculations
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    
    # Take element-wise maximum
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # Wilder's smoothing EMA (alpha = 1 / period)
    atr = tr.ewm(alpha=1.0 / period, adjust=False).mean()
    
    latest_atr = float(atr.iloc[-1])
    if np.isnan(latest_atr):
        latest_atr = 0.0
        
    return round(latest_atr, 2)
