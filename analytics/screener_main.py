import argparse
import os
import sys
import yaml
import datetime
import time
import json
import pytz

# Add current directory to path if not present to support running from outside analytics/
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.logger import log_info, log_error
from utils.validators import validate_config
from core.models import ScreenerRunResult, TradeSetup
from data.top_movers_fetcher import get_filtered_movers
from data.historical_fetcher import get_historical_candles
from data.intraday_fetcher import get_intraday_candles
from data.provider_client import DEFAULT_UNIVERSE
from indicators.rsi import calculate_rsi
from indicators.bollinger import calculate_bollinger_bands
from indicators.atr import calculate_atr
from indicators.swings import calculate_swings
from analytics.volatility_analyzer import analyze_volatility
from analytics.time_pattern_analyzer import analyze_time_patterns
from analytics.target_estimator import estimate_targets
from analytics.risk_analyzer import analyze_risk
from core.decision_engine import evaluate_setup
from exporters.json_exporter import export_to_json
from exporters.csv_exporter import export_to_csv


def is_nse_market_open():
    """Check if NSE market is currently open (09:15 - 15:30 IST, Mon-Fri)."""
    IST = pytz.timezone("Asia/Kolkata")
    now_ist = datetime.datetime.now(IST)
    weekday = now_ist.weekday()  # 0=Mon, 6=Sun
    if weekday >= 5:  # Saturday or Sunday
        return False
    market_open = now_ist.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close = now_ist.replace(hour=15, minute=30, second=0, microsecond=0)
    return market_open <= now_ist <= market_close


def get_custom_symbol_setups(symbols, config):
    """
    For custom symbol mode: fetch live data for the given symbols,
    compute percent move vs previous close, apply move threshold filter,
    and return TradeSetup objects.
    """
    import yfinance as yf
    import pandas as pd

    move_threshold = config.get("move_threshold", 1.5)
    setups = []
    scanned = 0
    filtered = 0

    log_info("CUSTOM_SYMBOLS", message=f"Fetching live data for {len(symbols)} custom symbols")

    for symbol in symbols:
        symbol = symbol.strip().upper()
        if not symbol:
            continue
        if "." not in symbol:
            symbol += ".NS"
        try:
            ticker = yf.Ticker(symbol)
            # Fetch last 5 days to get prev close
            df = ticker.history(period="5d", interval="1d")

            # Patch NaN last row using 1d live data
            if not df.empty and pd.isna(df.iloc[-1]['Close']):
                df_1d = ticker.history(period="1d")
                if not df_1d.empty and not pd.isna(df_1d.iloc[-1]['Close']):
                    last_idx = df.index[-1]
                    latest_idx = df_1d.index[-1]
                    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                        df.loc[last_idx, col] = df_1d.loc[latest_idx, col]

            # Drop rows with NaN close
            df = df.dropna(subset=['Close'])
            if len(df) < 2:
                log_info("CUSTOM_SYMBOLS", symbol=symbol, message="Not enough data rows, skipping")
                continue

            scanned += 1
            last_row = df.iloc[-1]
            prev_row = df.iloc[-2]
            current_price = float(last_row['Close'])
            prev_close = float(prev_row['Close'])
            if prev_close == 0:
                continue

            percent_move = ((current_price - prev_close) / prev_close) * 100
            day_open = float(last_row['Open'])
            day_high = float(last_row['High'])
            day_low = float(last_row['Low'])

            source_list = "TOP_GAINER" if percent_move >= 0 else "TOP_LOSER"
            trade_side = "LONG" if percent_move >= 0 else "SHORT"

            # Apply move threshold
            if abs(percent_move) >= move_threshold:
                setup = TradeSetup(
                    symbol=symbol,
                    source_list=source_list,
                    trade_side=trade_side,
                    current_price=current_price,
                    current_percent_move=percent_move,
                    day_open=day_open,
                    day_high=day_high,
                    day_low=day_low
                )
                setup.price_bucket_rule = f"custom_symbol_move_geq_{move_threshold}"
                setups.append(setup)
                filtered += 1
                log_info("CUSTOM_SYMBOLS", symbol=symbol,
                         message=f"Included: price={current_price:.2f}, move={percent_move:.2f}%")
            else:
                log_info("CUSTOM_SYMBOLS", symbol=symbol,
                         message=f"Filtered out: move {percent_move:.2f}% < threshold {move_threshold}%")

        except Exception as e:
            log_error("CUSTOM_SYMBOLS", symbol=symbol, error_message=str(e))

    return setups, scanned, filtered


def analyze_setups(setups, config, result):
    """Run full technical analysis on each setup and add to result."""
    import yfinance as yf
    import pandas as pd
    import numpy as np
    from utils.time_utils import calculate_median_time

    log_info("PROCESS_SETUPS", message=f"Starting analysis for {len(setups)} setups")
    if not setups:
        return

    # Extract all symbols
    symbols = [s.symbol for s in setups]
    symbols_str = " ".join(symbols)

    # 1. Batch download daily history
    lookback_days = config.get("lookback_days", 60)
    calendar_days = int(lookback_days * 1.5)
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=calendar_days)
    
    log_info("BATCH_DOWNLOAD", message=f"Downloading daily history for {len(symbols)} symbols")
    try:
        batch_hist = yf.download(symbols_str, start=start_date.strftime("%Y-%m-%d"), end=end_date.strftime("%Y-%m-%d"), interval="1d", group_by="ticker", progress=False)
    except Exception as e:
        log_error("BATCH_DOWNLOAD_HIST_ERR", error_message=str(e))
        batch_hist = pd.DataFrame()

    # 2. Batch download intraday history (cap at 59 days for yfinance 5m/15m)
    intraday_days = min(lookback_days, 59)
    log_info("BATCH_DOWNLOAD", message=f"Downloading intraday data ({config['intraday_interval']}) for last {intraday_days} days for {len(symbols)} symbols")
    try:
        batch_intra = yf.download(symbols_str, period=f"{intraday_days}d", interval=config["intraday_interval"], group_by="ticker", progress=False)
    except Exception as e:
        log_error("BATCH_DOWNLOAD_INTRA_ERR", error_message=str(e))
        batch_intra = pd.DataFrame()

    # Helper to extract a single ticker's DataFrame from a batch DataFrame
    def get_ticker_df(batch_df, ticker):
        if batch_df.empty:
            return pd.DataFrame()
        columns = batch_df.columns
        if isinstance(columns, pd.MultiIndex):
            if columns.names[0] == 'ticker' or (columns.levels and ticker in columns.levels[0]):
                try:
                    df = batch_df[ticker]
                    return df.dropna(subset=['Close'])
                except KeyError:
                    return pd.DataFrame()
            elif len(columns.levels) > 1 and ticker in columns.levels[1]:
                try:
                    df = batch_df.xs(ticker, axis=1, level=1)
                    return df.dropna(subset=['Close'])
                except KeyError:
                    return pd.DataFrame()
        else:
            return batch_df.dropna(subset=['Close'])

    for setup in setups:
        symbol = setup.symbol
        log_info("ANALYZE_SYMBOL", symbol=symbol, message="Processing indicators and variation data")

        hist_df = get_ticker_df(batch_hist, symbol)
        if hist_df.empty:
            hist_df = get_historical_candles(symbol, lookback_days)

        intraday_df = get_ticker_df(batch_intra, symbol)
        if intraday_df.empty:
            intraday_df = get_intraday_candles(symbol, config["intraday_interval"], days=intraday_days)

        if hist_df.empty:
            setup.warnings.append("Missing historical daily data")
            setup.final_decision = "REJECT"
            setup.decision_notes = ["Could not load historical daily candles"]
            result.total_rejected += 1
            result.setups.append(setup)
            continue

        hist_df = hist_df.tail(lookback_days)
        close_prices = hist_df['Close']

        # Determine trade side based on current percent move
        setup.trade_side = "LONG" if setup.current_percent_move >= 0 else "SHORT"
        setup.indicator = "Sell" if setup.current_percent_move >= 0 else "Buy"

        # Calculate daily indicators
        rsi_val, rsi_lbl = calculate_rsi(close_prices, config["rsi_period"])
        bb_upper, bb_mid, bb_lower, bb_state = calculate_bollinger_bands(
            close_prices, config["bollinger_period"], config["bollinger_stddev"])
        atr_val = calculate_atr(hist_df, config["atr_period"])

        setup.rsi_14 = rsi_val
        setup.rsi_label = rsi_lbl
        setup.bollinger_state = bb_state
        setup.atr_14 = atr_val

        # Swings Stop Reference
        swing_high, swing_low, fallback_stop = calculate_swings(intraday_df)
        setup.swing_stop_reference = fallback_stop

        # Lookup daily variation
        eligible_days = []

        if not intraday_df.empty:
            df = intraday_df.copy()
            df['DateOnly'] = df.index.date
            grouped = df.groupby('DateOnly')

            for date_val, day_df in grouped:
                if len(day_df) < 2:
                    continue
                day_open = float(day_df['Open'].iloc[0])
                day_close = float(day_df['Close'].iloc[-1])
                day_high = float(day_df['High'].max())
                day_low = float(day_df['Low'].min())

                # Daily variation %
                day_var_pct = ((day_high - day_low) / day_low) * 100 if day_low > 0 else 0.0

                # Stats relative to Open
                high_pct_from_open = ((day_high - day_open) / day_open) * 100 if day_open > 0 else 0.0
                low_pct_from_open = ((day_open - day_low) / day_open) * 100 if day_open > 0 else 0.0
                close_pct_from_open = ((day_close - day_open) / day_open) * 100 if day_open > 0 else 0.0

                # Determine the close threshold based on scan mode
                is_custom_mode = config.get("is_custom_mode", False)
                close_threshold = config.get("move_threshold", 1.5) if is_custom_mode else config.get("move_variance", 3.0)

                if day_var_pct >= abs(setup.current_percent_move) and abs(close_pct_from_open) <= close_threshold:
                    high_idx = day_df['High'].idxmax()
                    low_idx = day_df['Low'].idxmin()

                    high_time_str = high_idx.strftime("%H:%M")
                    low_time_str = low_idx.strftime("%H:%M")

                    eligible_days.append({
                        "date": date_val,
                        "open": day_open,
                        "close": day_close,
                        "high": day_high,
                        "low": day_low,
                        "high_time": high_time_str,
                        "low_time": low_time_str,
                        "high_pct": high_pct_from_open,
                        "low_pct": low_pct_from_open,
                        "close_pct": close_pct_from_open,
                        "variation": day_var_pct
                    })

        comp_count = len(eligible_days)
        setup.comparable_sample_count = comp_count
        setup.indicator_days = comp_count

        if comp_count == 0:
            is_custom_mode = config.get("is_custom_mode", False)
            close_threshold = config.get("move_threshold", 1.5) if is_custom_mode else config.get("move_variance", 3.0)
            setup.final_decision = "REJECT"
            setup.decision_notes = [f"No historical days met variation threshold of {abs(setup.current_percent_move):.2f}% and close threshold of {close_threshold:.2f}%"]
            setup.warnings.append("No eligible historical variation days")
            result.total_rejected += 1
            result.setups.append(setup)
            continue

        # Calculate Averages
        avg_high_pct = float(np.mean([d["high_pct"] for d in eligible_days]))
        avg_low_pct = float(np.mean([d["low_pct"] for d in eligible_days]))
        avg_close_pct = float(np.mean([abs(d["close_pct"]) for d in eligible_days]))
        avg_var_pct = float(np.mean([d["variation"] for d in eligible_days]))

        high_times = [d["high_time"] for d in eligible_days]
        low_times = [d["low_time"] for d in eligible_days]

        typical_high = calculate_median_time(high_times)
        typical_low = calculate_median_time(low_times)

        setup.typical_high_time = typical_high if typical_high != "N/A" else "10:30"
        setup.typical_low_time = typical_low if typical_low != "N/A" else "14:15"

        setup.avg_extension_percent = round(avg_var_pct, 2)
        setup.avg_close_percent = round(avg_close_pct, 2)
        setup.historical_max_gain_percent = round(float(np.max([d["variation"] for d in eligible_days])), 2)
        setup.historical_max_loss_percent = round(float(np.min([d["variation"] for d in eligible_days])), 2)
        setup.time_pattern_label = f"{comp_count} eligible days"

        # Expected Range relative to CMP
        expected_low = setup.current_price * (1.0 - avg_low_pct / 100.0)
        expected_high = setup.current_price * (1.0 + avg_high_pct / 100.0)

        setup.target_min = round(expected_low, 2)
        setup.target_max = round(expected_high, 2)
        setup.expected_exit_zone = round(setup.current_price * (1.0 + (avg_close_pct / 100.0) if setup.trade_side == "LONG" else 1.0 - (avg_close_pct / 100.0)), 2)

        # Risk Analysis
        target_for_risk_min = expected_high if setup.trade_side == "LONG" else expected_low
        target_for_risk_max = expected_high if setup.trade_side == "LONG" else expected_low

        stop_loss, stop_type, risk, reward, rr = analyze_risk(
            setup.current_price, target_for_risk_min, target_for_risk_max, atr_val, swing_high, swing_low,
            setup.trade_side, config["atr_multiplier"]
        )
        setup.stop_loss = stop_loss
        setup.stop_loss_type = stop_type
        setup.risk_amount = risk
        setup.reward_amount = reward
        setup.risk_reward_ratio = rr

        # Evaluate decision
        evaluate_setup(setup, config["min_risk_reward"], config["move_variance"], config["use_risk_reward_filter"])

        setup.decision_notes.append(f"Consolidated over {comp_count} eligible days with avg daily variation {avg_var_pct:.2f}%")

        if setup.final_decision in ["TRADE", "WATCHLIST"]:
            result.total_selected += 1
        else:
            result.total_rejected += 1

        result.setups.append(setup)
        log_info("ANALYZE_SYMBOL", symbol=symbol, status="SUCCESS",
                 message=f"Decision: {setup.final_decision}, RiskReward: {rr}")


def main():
    parser = argparse.ArgumentParser(description="V1 Intraday Stock Screener Analytics Engine")
    parser.add_argument("--config", default="config/screener_config.yaml", help="Path to YAML config file")
    parser.add_argument("--output", help="Path to export the output JSON snapshot file")
    parser.add_argument("--runId", help="Unique run identifier")

    # Overrides for request-specific filters
    parser.add_argument("--minPrice", type=float, help="Min price limit override")
    parser.add_argument("--maxPrice", type=float, help="Max price limit override")
    parser.add_argument("--minRiskReward", type=float, help="Min risk reward ratio override")
    parser.add_argument("--lookbackDays", type=int, help="Lookback days override")
    parser.add_argument("--intradayInterval", default="5m", help="Intraday interval (5m/15m) override")
    parser.add_argument("--moveThreshold", type=float, help="Min move percent threshold override")
    parser.add_argument("--moveVariance", type=float, help="Variance percent threshold override")
    parser.add_argument("--useRiskRewardFilter", default="true", help="Whether to apply the risk-reward filter")

    # Custom symbol mode
    parser.add_argument("--symbols", type=str, default="",
                        help="Comma-separated list of NSE symbols for targeted scan (e.g. HSCL.NS,RELIANCE.NS)")

    args = parser.parse_args()

    # Load configuration
    config_path = args.config
    # Fallback to local path relative to script if not found directly
    if not os.path.exists(config_path):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, args.config)

    config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
            log_info("CONFIG_LOAD", status="SUCCESS", message=f"Loaded configuration from {config_path}")
        except Exception as e:
            log_error("CONFIG_LOAD", error_message=f"Failed to parse config: {str(e)}")
            sys.exit(1)
    else:
        log_info("CONFIG_LOAD", status="WARNING", message=f"Config file not found at {config_path}. Using defaults.")

    # Apply command-line overrides
    if args.minPrice is not None:
        config["min_price"] = args.minPrice
    if args.maxPrice is not None:
        config["max_price"] = args.maxPrice
    if args.minRiskReward is not None:
        config["min_risk_reward"] = args.minRiskReward
    if args.lookbackDays is not None:
        config["lookback_days"] = args.lookbackDays
    if args.intradayInterval is not None:
        config["intraday_interval"] = args.intradayInterval
    if args.moveThreshold is not None:
        config["move_threshold"] = args.moveThreshold
    if args.moveVariance is not None:
        config["move_variance"] = args.moveVariance
    if args.useRiskRewardFilter is not None:
        config["use_risk_reward_filter"] = (args.useRiskRewardFilter.lower() == "true")

    # Apply default values if not present
    config.setdefault("use_risk_reward_filter", True)
    config.setdefault("lookback_days", 60)
    config.setdefault("min_price", 500.0)
    config.setdefault("max_price", 2750.0)
    config.setdefault("move_threshold", 1.5)
    config.setdefault("move_variance", 3.0)
    config.setdefault("rsi_period", 14)
    config.setdefault("bollinger_period", 20)
    config.setdefault("bollinger_stddev", 2.0)
    config.setdefault("atr_period", 14)
    config.setdefault("atr_multiplier", 1.5)
    config.setdefault("min_risk_reward", 0.1)
    config.setdefault("intraday_interval", "5m")
    config.setdefault("snapshot_output_dir", "../output/runs")

    # Validate configurations
    try:
        validate_config(config)
    except ValueError as e:
        log_error("VALIDATE_CONFIG", error_message=str(e))
        sys.exit(1)

    # Determine scan mode: custom symbols or full universe
    custom_symbols_raw = args.symbols.strip() if args.symbols else ""
    is_custom_mode = bool(custom_symbols_raw)
    config["is_custom_mode"] = is_custom_mode
    custom_symbols = []
    if is_custom_mode:
        for s in custom_symbols_raw.split(","):
            sym = s.strip().upper()
            if sym:
                if "." not in sym:
                    sym += ".NS"
                custom_symbols.append(sym)

    # Setup Run result metadata
    run_id = args.runId or datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    run_time = datetime.datetime.now().astimezone().isoformat()
    result = ScreenerRunResult(run_id=run_id, run_time=run_time, config_version="v1")

    if is_custom_mode:
        # ── Custom Symbol Mode ─────────────────────────────────────────────
        log_info("SCAN_MODE", message=f"Custom symbol mode: {custom_symbols}")
        setups, scanned, filtered = get_custom_symbol_setups(custom_symbols, config)
        result.total_scanned = scanned
        result.total_filtered = filtered
    else:
        # ── Nifty Universe Mode ────────────────────────────────────────────
        market_open = is_nse_market_open()
        log_info("SCAN_MODE", message=f"Nifty universe mode. Market open: {market_open}")
        setups, scanned, filtered = get_filtered_movers(config)
        result.total_scanned = scanned
        result.total_filtered = filtered

    # Run full technical analysis on filtered setups
    analyze_setups(setups, config, result)

    # 3. Export snapshots
    # Output path resolution
    output_json = args.output
    if not output_json:
        # Resolve from config directory
        out_dir = config["snapshot_output_dir"]
        if not os.path.isabs(out_dir):
            # relative to workspace
            out_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), out_dir))
        output_json = os.path.join(out_dir, f"{run_id}-run.json")
        latest_json_path = os.path.join(out_dir, "latest.json")
        latest_csv_path = os.path.join(out_dir, "latest.csv")
    else:
        latest_json_path = output_json
        latest_csv_path = output_json.replace(".json", ".csv")

    # Save timestamped run file always
    export_to_json(result, output_json)
    export_to_csv(result, output_json.replace(".json", ".csv"))

    if not args.output:
        # Always overwrite latest.json/csv to ensure the UI remains in sync with the last run
        export_to_json(result, latest_json_path)
        export_to_csv(result, latest_csv_path)
        log_info("SNAPSHOT", message="latest.json updated with current run")

    # Return structured JSON to stdout so Java can capture it directly
    sys.stdout.flush()
    # Print a boundary marker to isolate the JSON payload from logger statements
    print("---JSON_OUTPUT_START---")
    print(json.dumps(result.to_dict()))
    print("---JSON_OUTPUT_END---")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
