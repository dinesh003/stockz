def validate_config(config):
    errors = []
    
    # Check lookback
    lookback = config.get("lookback_days", 60)
    if lookback < 20:
        errors.append("lookback_days must be at least 20")
        
    # Check prices
    min_price = config.get("min_price", 500.0)
    max_price = config.get("max_price", 2750.0)
    if min_price >= max_price:
        errors.append("min_price must be strictly less than max_price")
        
    # Check risk reward
    if config.get("use_risk_reward_filter", True):
        min_rr = config.get("min_risk_reward", 2.0)
        if min_rr <= 0:
            errors.append("min_risk_reward must be greater than 0")
        
    # Check move threshold and variance
    move_threshold = config.get("move_threshold", 5.0)
    if move_threshold < 0:
        errors.append("move_threshold must be greater than or equal to 0")
        
    move_variance = config.get("move_variance", 3.0)
    if move_variance < 0:
        errors.append("move_variance must be greater than or equal to 0")
        
    if errors:
        raise ValueError("; ".join(errors))
    return True
