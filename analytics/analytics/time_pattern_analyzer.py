import pandas as pd
import datetime
from utils.time_utils import calculate_median_time, time_to_minutes
from utils.logger import log_info, log_error

def analyze_time_patterns(intraday_df: pd.DataFrame, comp_dates: list, trade_side: str) -> tuple[str, str, str]:
    """
    Analyzes intraday candles to find typical times for highs and lows.
    Returns:
    - (median_high_time: str, median_low_time: str, pattern_label: str)
    """
    if intraday_df.empty:
        return "10:30", "14:15", "EARLY_BREAKOUT"
        
    # Group intraday data by calendar date
    # yfinance intraday index is DatetimeIndex
    df = intraday_df.copy()
    df['DateOnly'] = df.index.date
    
    # Filter for comp_dates if available in intraday data
    comp_dates_set = {d.date() if hasattr(d, 'date') else pd.to_datetime(d).date() for d in comp_dates}
    
    available_dates = df['DateOnly'].unique()
    matching_dates = [d for d in available_dates if d in comp_dates_set]
    
    # Fallback to all available recent days if no match
    target_dates = matching_dates if matching_dates else available_dates
    
    high_times = []
    low_times = []
    
    for date_val in target_dates:
        day_df = df[df['DateOnly'] == date_val]
        if day_df.empty:
            continue
            
        # Find time of high and low
        high_idx = day_df['High'].idxmax()
        low_idx = day_df['Low'].idxmin()
        
        # Format as HH:MM
        high_time_str = high_idx.strftime("%H:%M")
        low_time_str = low_idx.strftime("%H:%M")
        
        high_times.append(high_time_str)
        low_times.append(low_time_str)
        
    median_high = calculate_median_time(high_times)
    median_low = calculate_median_time(low_times)
    
    # If calculate_median_time failed, use default
    if median_high == "N/A":
        median_high = "10:30"
    if median_low == "N/A":
        median_low = "14:15"
        
    # Classification rules
    m_high = time_to_minutes(median_high)
    m_low = time_to_minutes(median_low)
    
    # Market Open is 09:15 AM (555 minutes), Market Close is 03:30 PM (930 minutes)
    if trade_side == "LONG":
        if m_high < 690 and m_low > 750:  # before 11:30 AM and after 12:30 PM
            pattern = "MIDDAY_FADE"
        elif m_high >= 840: # after 02:00 PM
            pattern = "LATE_CONTINUATION"
        elif m_high < 645: # before 10:45 AM
            pattern = "EARLY_BREAKOUT"
        else:
            pattern = "VOLATILE_REVERSAL"
    else: # SHORT
        if m_low < 690 and m_high > 750:  # before 11:30 AM and after 12:30 PM
            pattern = "MIDDAY_FADE"
        elif m_low >= 840: # after 02:00 PM
            pattern = "LATE_CONTINUATION"
        elif m_low < 645: # before 10:45 AM
            pattern = "EARLY_BREAKOUT"
        else:
            pattern = "VOLATILE_REVERSAL"
            
    return median_high, median_low, pattern
