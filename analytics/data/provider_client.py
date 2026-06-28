import yfinance as yf
import pandas as pd
import datetime
from utils.logger import log_info, log_error

# Curated liquid NSE tickers list (Nifty 100/200 representatives)
DEFAULT_UNIVERSE = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "BHARTIARTL.NS", "ICICIBANK.NS",
    "INFY.NS", "SBIN.NS", "HINDUNILVR.NS", "ITC.NS", "LT.NS",
    "BAJFINANCE.NS", "HCLTECH.NS", "MARUTI.NS", "SUNPHARMA.NS", "ADANIENT.NS",
    "KOTAKBANK.NS", "TITAN.NS", "ULTRACEMCO.NS", "ONGC.NS", "NTPC.NS",
    "COALINDIA.NS", "TATASTEEL.NS", "AXISBANK.NS", "ADANIPORTS.NS", "ASIANPAINT.NS",
    "M&M.NS", "JSWSTEEL.NS", "POWERGRID.NS", "HINDALCO.NS", "TATAMOTORS.NS",
    "GRASIM.NS", "WIPRO.NS", "NESTLEIND.NS", "SBILIFE.NS", "IOC.NS",
    "HAL.NS", "BAJAJFINSV.NS", "DLF.NS", "TRENT.NS", "EICHERMOT.NS",
    "SHRIRAMFIN.NS", "INDUSINDBK.NS", "TECHM.NS", "BPCL.NS", "CIPLA.NS",
    "HEROMOTOCO.NS", "BRITANNIA.NS", "DIVISLAB.NS", "DRREDDY.NS", "APOLLOHOSP.NS",
    "TATACONSUM.NS", "BAJAJ-AUTO.NS", "HDFCLIFE.NS", "BEL.NS", "PNB.NS",
    "ZOMATO.NS", "JINDALSTEL.NS", "LTIM.NS", "TATAELXSI.NS", "PIDILITIND.NS",
    "HAVELLS.NS", "GAIL.NS", "SRF.NS", "ICICIPRULI.NS", "SIEMENS.NS",
    "ABB.NS", "BOSCHLTD.NS", "TORNTPHARM.NS", "MUTHOOTFIN.NS", "COLPAL.NS",
    "ASHOKLEY.NS", "TVSMOTOR.NS", "UBL.NS", "MCDOWELL-N.NS", "HINDPETRO.NS",
    "MRF.NS", "PAGEIND.NS", "BALKRISIND.NS", "AUBANK.NS", "BANDHANBNK.NS",
    "MAXHEALTH.NS", "IRCTC.NS", "RECLTD.NS", "PFC.NS", "POLYCAB.NS",
    "KEI.NS", "DIXON.NS", "IPCALAB.NS", "GLENMARK.NS", "LICHSGFIN.NS"
]

def fetch_current_market_data(tickers=None):
    """
    Downloads daily data for a list of tickers to determine daily movers.
    Fetches 2 days of history to calculate percent move from previous close.
    """
    if not tickers:
        tickers = DEFAULT_UNIVERSE
        
    log_info("FETCH_MOVERS", message=f"Downloading current daily data for {len(tickers)} tickers")
    
    start_time = datetime.datetime.now()
    try:
        # Download multiple tickers at once
        tickers_str = " ".join(tickers)
        data = yf.download(tickers_str, period="5d", group_by="ticker", progress=False)
        
        # Download latest 1d data to patch any NaN values in the latest row (Yahoo Finance API international market daily data bug)
        try:
            data_latest = yf.download(tickers_str, period="1d", group_by="ticker", progress=False)
            if not data.empty and not data_latest.empty:
                last_idx = data.index[-1]
                latest_idx = data_latest.index[-1]
                if isinstance(data.columns, pd.MultiIndex):
                    if data.columns.names[0] == 'ticker' or (data.columns.levels and data.columns.levels[0][0].endswith('.NS')):
                        unique_tickers = list(data.columns.levels[0])
                        for ticker in unique_tickers:
                            if ticker in data_latest.columns.levels[0]:
                                if pd.isna(data.loc[last_idx, (ticker, 'Close')]):
                                    if not pd.isna(data_latest.loc[latest_idx, (ticker, 'Close')]):
                                        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                                            data.loc[last_idx, (ticker, col)] = data_latest.loc[latest_idx, (ticker, col)]
                    else:
                        unique_tickers = list(data.columns.levels[1])
                        for ticker in unique_tickers:
                            if ticker in data_latest.columns.levels[1]:
                                if pd.isna(data.loc[last_idx, ('Close', ticker)]):
                                    if not pd.isna(data_latest.loc[latest_idx, ('Close', ticker)]):
                                        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                                            data.loc[last_idx, (col, ticker)] = data_latest.loc[latest_idx, (col, ticker)]
        except Exception as patch_ex:
            log_error("PATCH_MOVERS_WARN", error_message=f"Failed to patch movers with 1d data: {str(patch_ex)}")
            
        elapsed = int((datetime.datetime.now() - start_time).total_seconds() * 1000)
        log_info("FETCH_MOVERS", status="SUCCESS", elapsed_ms=elapsed, message="Completed tickers download")
        return data
    except Exception as e:
        log_error("FETCH_MOVERS", error_message=str(e))
        return pd.DataFrame()

def fetch_historical_daily_candles(symbol, lookback_days=60):
    """
    Downloads historical daily candles for a single symbol.
    We request slightly more days to account for weekends/market holidays.
    """
    # 60 trading days is roughly 90 calendar days
    calendar_days = int(lookback_days * 1.5)
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=calendar_days)
    
    log_info("FETCH_HISTORY", symbol=symbol, message=f"Downloading daily history from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    start_time = datetime.datetime.now()
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date.strftime("%Y-%m-%d"), end=end_date.strftime("%Y-%m-%d"), interval="1d")
        elapsed = int((datetime.datetime.now() - start_time).total_seconds() * 1000)
        
        # Patch latest row if Close is NaN using 1d ticker history
        if not df.empty:
            last_idx = df.index[-1]
            if pd.isna(df.loc[last_idx, 'Close']):
                try:
                    df_latest = ticker.history(period="1d")
                    if not df_latest.empty:
                        latest_idx = df_latest.index[-1]
                        if not pd.isna(df_latest.loc[latest_idx, 'Close']):
                            for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                                df.loc[last_idx, col] = df_latest.loc[latest_idx, col]
                except Exception as patch_ex:
                    log_error("PATCH_HISTORY_WARN", symbol=symbol, error_message=f"Failed to patch history with 1d data: {str(patch_ex)}")
                    
        # Keep only the last lookback_days
        if not df.empty:
            df = df.tail(lookback_days)
            
        log_info("FETCH_HISTORY", symbol=symbol, status="SUCCESS", elapsed_ms=elapsed, message=f"Loaded {len(df)} daily candles")
        return df
    except Exception as e:
        log_error("FETCH_HISTORY", symbol=symbol, error_message=str(e))
        return pd.DataFrame()

def fetch_intraday_candles(symbol, interval="5m", days=5):
    """
    Downloads intraday candles for swing high/low and time pattern analysis.
    yfinance supports 5m interval for last 60 days, and 15m for last 60 days.
    """
    log_info("FETCH_INTRADAY", symbol=symbol, message=f"Downloading intraday data ({interval}) for last {days} days")
    
    start_time = datetime.datetime.now()
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=f"{days}d", interval=interval)
        elapsed = int((datetime.datetime.now() - start_time).total_seconds() * 1000)
        
        log_info("FETCH_INTRADAY", symbol=symbol, status="SUCCESS", elapsed_ms=elapsed, message=f"Loaded {len(df)} intraday candles")
        return df
    except Exception as e:
        log_error("FETCH_INTRADAY", symbol=symbol, error_message=str(e))
        return pd.DataFrame()
