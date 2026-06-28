def analyze_risk(entry_price: float, target_min: float, target_max: float, atr: float, swing_high: float, swing_low: float, trade_side: str, atr_multiplier: float = 1.5) -> tuple[float, str, float, float, float]:
    """
    Computes stop-loss, risk amount, reward amount, and risk-reward ratio.
    
    Returns:
    - (stop_loss: float, stop_loss_type: str, risk_amount: float, reward_amount: float, rr_ratio: float)
    """
    stop_loss_type = "ATR"
    
    # 1. Compute stop-loss
    if atr > 0:
        if trade_side == "LONG":
            stop_loss = entry_price - (atr_multiplier * atr)
            # Stop loss must be below entry
            if stop_loss >= entry_price:
                stop_loss = entry_price * 0.985
        else: # SHORT
            stop_loss = entry_price + (atr_multiplier * atr)
            # Stop loss must be above entry
            if stop_loss <= entry_price:
                stop_loss = entry_price * 1.015
    else:
        # Use swing-based stop-loss if ATR is not available
        stop_loss_type = "SWING"
        if trade_side == "LONG":
            stop_loss = swing_low if swing_low > 0 and swing_low < entry_price else entry_price * 0.98
        else: # SHORT
            stop_loss = swing_high if swing_high > entry_price else entry_price * 1.02
            
    # Ensure stop_loss is positive
    stop_loss = max(stop_loss, 0.01)
    
    # 2. Compute risk and reward amounts
    risk_amount = abs(entry_price - stop_loss)
    
    # We define reward relative to the closer target (conservative approach)
    if trade_side == "LONG":
        reward_amount = abs(target_min - entry_price)
    else: # SHORT
        reward_amount = abs(target_max - entry_price)
        
    # 3. Compute Risk-Reward Ratio
    if risk_amount > 0:
        rr_ratio = reward_amount / risk_amount
    else:
        rr_ratio = 0.0
        
    return round(stop_loss, 2), stop_loss_type, round(risk_amount, 2), round(reward_amount, 2), round(rr_ratio, 2)
