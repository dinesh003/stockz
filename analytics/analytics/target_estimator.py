def estimate_targets(entry_price: float, today_move: float, avg_extension: float, avg_close: float, trade_side: str) -> tuple[float, float, float]:
    """
    Estimates target_min, target_max, and expected_exit_zone.
    Values are computed relative to the previous day's close.
    """
    # Calculate previous day's close
    prev_close = entry_price / (1.0 + today_move / 100.0)
    
    # We define target_min as the numerically smaller value and target_max as the numerically larger value
    if trade_side == "LONG":
        # Target range is centered around the avg_extension
        # Let's say +/- 0.5% of the extension
        ext_min_pct = max(avg_extension - 0.5, today_move + 0.5)
        ext_max_pct = ext_min_pct + 1.0
        
        target_min = prev_close * (1.0 + ext_min_pct / 100.0)
        target_max = prev_close * (1.0 + ext_max_pct / 100.0)
        expected_exit = prev_close * (1.0 + avg_close / 100.0)
        
        # Ensure targets are above entry price
        if target_min <= entry_price:
            target_min = entry_price * 1.015
            target_max = entry_price * 1.025
            
    else: # SHORT
        # Target range (prices are lower than entry)
        # Numerically, target_min is the lower price (further target), target_max is the higher price (closer target)
        ext_max_pct = max(avg_extension - 0.5, abs(today_move) + 0.5) # max drop percentage
        ext_min_pct = ext_max_pct + 1.0
        
        target_min = prev_close * (1.0 - ext_min_pct / 100.0) # lower price (further)
        target_max = prev_close * (1.0 - ext_max_pct / 100.0) # higher price (closer)
        expected_exit = prev_close * (1.0 - avg_close / 100.0)
        
        # Ensure targets are below entry price
        if target_max >= entry_price:
            target_max = entry_price * 0.985
            target_min = entry_price * 0.975
            
    return round(target_min, 2), round(target_max, 2), round(expected_exit, 2)
