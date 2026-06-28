import pandas as pd
from data.provider_client import fetch_current_market_data
from core.rules import passes_price_move_filter
from core.models import TradeSetup
from utils.logger import log_info, log_error

def get_filtered_movers(config, tickers=None):
    """
    Fetches daily data for the ticker universe, calculates percentage moves,
    applies the price/move rules, and returns list of TradeSetup objects.
    """
    min_price = config.get("min_price", 500.0)
    max_price = config.get("max_price", 2750.0)
    move_threshold = config.get("move_threshold", 5.0)

    df_raw = fetch_current_market_data(tickers)
    if df_raw.empty:
        log_error("GET_MOVERS", error_message="Empty daily data dataframe returned from provider")
        return [], 0, 0
        
    setups = []
    scanned_count = 0
    filtered_count = 0
    
    # yfinance multi-index columns handling
    # Columns could be: (ticker, field) if group_by='ticker'
    # or (field, ticker) if group_by='column'
    columns = df_raw.columns
    if isinstance(columns, pd.MultiIndex):
        if columns.names[0] == 'ticker' or (columns.levels and columns.levels[0][0].endswith('.NS')):
            # Tickers are at level 0
            unique_tickers = list(columns.levels[0])
            grouped_by_ticker = True
        else:
            # Tickers are at level 1
            unique_tickers = list(columns.levels[1])
            grouped_by_ticker = False
    else:
        # Single ticker case or flat index
        log_error("GET_MOVERS", error_message="Unexpected flat columns in downloaded data")
        return [], 0, 0

    log_info("GET_MOVERS", message=f"Parsing data for {len(unique_tickers)} tickers")
    
    for ticker in unique_tickers:
        try:
            # Extract ticker specific series
            if grouped_by_ticker:
                ticker_df = df_raw[ticker]
            else:
                ticker_df = df_raw.xs(ticker, axis=1, level=1)
                
            # Drop rows where all elements are NaN for this ticker
            ticker_df = ticker_df.dropna(subset=['Close', 'Open'])
            if len(ticker_df) < 2:
                continue
                
            scanned_count += 1
            
            # Last row contains today's live/latest candle
            last_row = ticker_df.iloc[-1]
            prev_row = ticker_df.iloc[-2]
            
            current_price = float(last_row['Close'])
            prev_close = float(prev_row['Close'])
            
            if prev_close == 0:
                continue
                
            percent_move = ((current_price - prev_close) / prev_close) * 100
            day_open = float(last_row['Open'])
            day_high = float(last_row['High'])
            day_low = float(last_row['Low'])
            
            # Determine source list based on move direction
            source_list = "TOP_GAINER" if percent_move >= 0 else "TOP_LOSER"
            trade_side = "LONG" if percent_move >= 0 else "SHORT"
            
            # Calculate today's high-low variation %
            today_variation = ((day_high - day_low) / day_low) * 100 if day_low > 0 else 0.0
            
            # Apply business rules dynamically based on today's high-low variation % and Var% (move_variance)
            move_variance = config.get("move_variance", 3.0)
            passed, rule_label = passes_price_move_filter(
                current_price, today_variation,
                min_price=min_price, max_price=max_price,
                move_threshold=move_variance
            )
            
            if passed:
                setup = TradeSetup(
                    symbol=ticker,
                    source_list=source_list,
                    trade_side=trade_side,
                    current_price=current_price,
                    current_percent_move=percent_move,
                    day_open=day_open,
                    day_high=day_high,
                    day_low=day_low
                )
                setup.price_bucket_rule = rule_label
                setups.append(setup)
                filtered_count += 1
                
        except Exception as e:
            # Ignore individual ticker parse errors and log
            log_error("GET_MOVERS", symbol=ticker, error_message=f"Error parsing ticker daily data: {str(e)}")
            
    log_info("GET_MOVERS", status="SUCCESS", message=f"Scanned: {scanned_count}, Passed Filter: {filtered_count}")
    return setups, scanned_count, filtered_count
