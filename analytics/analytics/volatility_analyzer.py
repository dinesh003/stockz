import pandas as pd
import numpy as np
from utils.logger import log_info, log_error

def analyze_volatility(df: pd.DataFrame, today_move: float, trade_side: str) -> tuple[float, float, float, float, int, list[pd.Timestamp]]:
    """
    Finds historical days in the 60-day dataset where absolute move exceeded abs(today_move).
    Computes volatility metrics from those comparable sessions.
    
    Returns:
    - (hist_max_gain: float, hist_max_loss: float, avg_extension: float, avg_close: float, sample_count: int, trigger_dates: list)
    """
    if len(df) < 2:
        return 0.0, 0.0, abs(today_move), abs(today_move), 0, []
        
    # Calculate daily returns, high returns, and low returns for historical candles
    # PrevClose is shifted Close
    prev_close = df['Close'].shift(1)
    
    daily_close_pct = ((df['Close'] - prev_close) / prev_close) * 100
    daily_high_pct = ((df['High'] - prev_close) / prev_close) * 100
    daily_low_pct = ((df['Low'] - prev_close) / prev_close) * 100
    
    # Absolute daily close return
    abs_daily_close_pct = daily_close_pct.abs()
    threshold = abs(today_move)
    history_close_pct = daily_close_pct.iloc[:-1]
    
    if trade_side == "LONG":
        comp_mask = history_close_pct >= threshold
    else:
        comp_mask = history_close_pct <= -threshold
    
    comp_indices = comp_mask[comp_mask].index
    sample_count = len(comp_indices)
    
    if sample_count == 0:
        # Fallback: take days where absolute move >= 2.0% in same direction
        if trade_side == "LONG":
            comp_mask = history_close_pct >= 2.0
        else:
            comp_mask = history_close_pct <= -2.0
        comp_indices = comp_mask[comp_mask].index
        sample_count = len(comp_indices)
        
    if sample_count == 0:
        # If still no days, return defaults
        return 0.0, 0.0, threshold, threshold, 0, []
        
    comp_highs = daily_high_pct.loc[comp_indices]
    comp_lows = daily_low_pct.loc[comp_indices]
    comp_closes = daily_close_pct.loc[comp_indices]
    
    # Compute signed stats
    if trade_side == "LONG":
        # Max gain = high percent, Max loss = low percent (drawdown)
        hist_max_gain = float(comp_highs.mean())
        hist_max_loss = float(comp_lows.mean())
        avg_extension = float(comp_highs.mean())
        avg_close = float(comp_closes.mean())
    else: # SHORT
        # Max gain = low percent (as a negative value), Max loss = high percent
        hist_max_gain = float(comp_lows.mean())
        hist_max_loss = float(comp_highs.mean())
        avg_extension = float(comp_lows.abs().mean())
        avg_close = float(comp_closes.abs().mean())
        
    # Clean up NaNs
    hist_max_gain = 0.0 if np.isnan(hist_max_gain) else hist_max_gain
    hist_max_loss = 0.0 if np.isnan(hist_max_loss) else hist_max_loss
    avg_extension = threshold if np.isnan(avg_extension) else avg_extension
    avg_close = threshold if np.isnan(avg_close) else avg_close
    
    # List of trigger dates
    trigger_dates = list(comp_indices)
    
    return round(hist_max_gain, 2), round(hist_max_loss, 2), round(avg_extension, 2), round(avg_close, 2), sample_count, trigger_dates
