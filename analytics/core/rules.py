def passes_price_move_filter(price: float, percent_move: float, 
                             min_price: float = 500.0, max_price: float = 2750.0, 
                             move_threshold: float = 5.0) -> tuple[bool, str]:
    """
    Checks if a stock meets price and daily move requirements.
    
    Returns:
    - (passed: bool, rule_label: str)
    """
    abs_move = abs(percent_move)
    
    if price < min_price or price > max_price:
        return False, "REJECT_PRICE_OUT_OF_BOUNDS"
        
    if abs_move >= move_threshold:
        return True, f"price_in_bounds_and_move_geq_{move_threshold}"
    else:
        return False, "REJECT_MOVE_INSUFFICIENT"
