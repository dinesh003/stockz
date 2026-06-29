from core.models import TradeSetup

def evaluate_setup(setup: TradeSetup, min_rr: float = 2.0, move_variance: float = 3.0, use_rr_filter: bool = True) -> None:
    """
    Evaluates indicators, risk/reward metrics, and comparable sample counts to assign
    the final classification: "TRADE", "WATCHLIST", or "REJECT".
    Populates decision_notes and warnings on the setup object.
    """
    notes = []
    warnings = []
    
    # 1. Check if we have historical comparable sessions
    if setup.comparable_sample_count == 0:
        setup.final_decision = "REJECT"
        setup.decision_notes = ["No comparable historical sessions found for this move percentage"]
        return
        
    if setup.comparable_sample_count < 3:
        warnings.append(f"Low comparable session count ({setup.comparable_sample_count})")
        notes.append("Comparable history sample size is small")
        
    # 2. Check RSI and Bollinger Bands confirmations
    rsi_ok = False
    bb_ok = False
    
    if setup.trade_side == "LONG":
        if setup.rsi_label == "BULLISH":
            rsi_ok = True
            notes.append("RSI confirms bullish momentum")
        elif setup.rsi_label == "NEUTRAL":
            notes.append("RSI is neutral")
        else:
            notes.append("RSI indicates bearish momentum on LONG setup")
            
        if setup.bollinger_state in ["UPPER_BAND_BREAKOUT", "UPPER_BAND_TOUCH"]:
            bb_ok = True
            notes.append(f"Price is pressing upper band ({setup.bollinger_state})")
        else:
            notes.append("Price is inside Bollinger Bands")
            
    else:  # SHORT
        if setup.rsi_label == "BEARISH":
            rsi_ok = True
            notes.append("RSI confirms bearish momentum")
        elif setup.rsi_label == "NEUTRAL":
            notes.append("RSI is neutral")
        else:
            notes.append("RSI indicates bullish momentum on SHORT setup")
            
        if setup.bollinger_state in ["LOWER_BAND_BREAKDOWN", "LOWER_BAND_TOUCH"]:
            bb_ok = True
            notes.append(f"Price is pressing lower band ({setup.bollinger_state})")
        else:
            notes.append("Price is inside Bollinger Bands")
            
    # 3. Evaluate Risk-Reward Ratio
    rr = setup.risk_reward_ratio
    
    # Historical extension vs current price check
    if setup.avg_extension_percent > abs(setup.current_percent_move):
        notes.append("Historical extension supports further move")
    else:
        notes.append("Current move is already at or near historical average extension limit")
        
    # 4. Final Classification Logic
    watchlist_threshold = min(1.2, min_rr) if use_rr_filter else 0.0
    if (not use_rr_filter or rr >= min_rr) and (rsi_ok or bb_ok):
        setup.final_decision = "TRADE"
        if use_rr_filter:
            notes.append(f"Setup meets minimum risk-reward ratio of {min_rr} with technical confirmation")
        else:
            notes.append("Setup has technical confirmation (Risk-reward filter disabled)")
    elif not use_rr_filter or rr >= watchlist_threshold:
        setup.final_decision = "WATCHLIST"
        if use_rr_filter and rr < min_rr:
            notes.append(f"Risk reward ratio ({rr}) is below target threshold ({min_rr})")
        if not (rsi_ok or bb_ok):
            notes.append("Technical indicators are neutral or do not confirm momentum")
    else:
        setup.final_decision = "REJECT"
        if use_rr_filter and rr < watchlist_threshold:
            notes.append(f"Risk reward ratio ({rr}) is too low (below {watchlist_threshold})")
        else:
            notes.append("Fails core technical indicator and momentum confirmations")
            
    # 5. Reversal Risk check using variance
    reversal_percent = setup.avg_extension_percent - setup.avg_close_percent
    if reversal_percent >= move_variance:
        warnings.append(f"High historical reversal risk ({reversal_percent:.2f}% vs threshold {move_variance}%)")
        notes.append(f"Historical average reversal is {reversal_percent:.2f}% (Avg Extension {setup.avg_extension_percent}%, Avg Close {setup.avg_close_percent}%). Expecting intraday reversal.")
            
    setup.decision_notes = notes
    setup.warnings = warnings
