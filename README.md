# StockZ - Intraday Stock Screener (V1)

StockZ is a lightweight, real-time intraday stock-picking and screening application. It automatically scans market movers (Top Gainers and Top Losers) on the Indian Stock Market (NSE), fetches recent historical behavior and intraday candle data, computes key technical indicators, estimates targets and stop-losses, and highlights high probability setups on a premium dark mode web dashboard.

V1 operates in **Snapshot Mode** without database overhead. All screening runs compute metrics in memory and save JSON and CSV snapshots directly to the local disk.

---

## Key Features
- **Live Market Movers Scanner**: Automatically evaluates daily movers from a pre-configured liquid NSE ticker list (e.g. Nifty 100 universe) using the free Yahoo Finance library (`yfinance`).
- **Deterministic Screening Rules**:
  - Rejects stocks priced at or below ₹500 or above ₹2,750.
  - Require at least a **10% move** for low-priced stocks (₹500 - ₹1,000).
  - Require at least a **4% move** for high-priced stocks (₹1,000 - ₹2,750).
- **Technical Confirmation Core**:
  - Calculates 14-period Relative Strength Index (RSI) with Wilder's smoothing.
  - Calculates 20,2 Bollinger Bands to detect breakouts and touches.
  - Calculates 14-period Average True Range (ATR) for risk spacing.
  - Calculates recent intraday swing highs and lows as structural support levels.
- **Comparable Volatility Analysis**: Evaluates lookback daily candles (60 days) to identify days where historical absolute moves exceeded the current day's move. Computes max historical gains/losses and average extensions.
- **Intraday Timing Analyzer**: Computes the typical time of day when highs and lows occur during comparable sessions. Classifies sessions into time patterns (`EARLY_BREAKOUT`, `MIDDAY_FADE`, `LATE_CONTINUATION`, `VOLATILE_REVERSAL`).
- **Dynamic Trade Setup Planner**: Automatically spaces stop-losses (ATR or structural swing-based), target ranges, and expected exit zones. Validates setup quality using a minimum Risk-Reward ratio (default 2.0).
- **Premium Dark Mode Dashboard**: An interactive browser cockpit with loading indicators, quick stat cards, shortlisted stocks table, and click-to-open detail drawers.

---

## Project Structure
```
stockz/
├── .gitignore              # Git ignore rules (configured to ignore output/ runs, compiled code, etc.)
├── README.md               # This usability documentation
├── analytics/              # Python Core Analytics Engine
│   ├── screener_main.py    # Main CLI entry point
│   ├── requirements.txt    # Python library requirements
│   ├── analytics/          # Volatility, risk, target, and timing analyzers
│   ├── config/             # Parameter config file (screener_config.yaml)
│   ├── core/               # Models, business rules, and decision engine
│   ├── data/               # Providers wrapper (yfinance fetchers)
│   ├── exporters/          # JSON and CSV output snapshot writers
│   ├── indicators/         # RSI, Bollinger, ATR, and Swings calculators
│   └── utils/              # Logger, validator, and time utility functions
├── backend/                # Spring Boot REST API Layer
│   ├── build.gradle        # Gradle build configuration
│   ├── src/main/java/      # Java classes (Controllers, DTOs, Services)
│   └── src/main/resources/ # application.properties & UI HTML/CSS/JS assets
└── output/
    └── runs/               # Local snapshot storage (latest.json, latest.csv)
```

---

## Prerequisites
Ensure the following tools are installed on your machine:
1. **Java 17 (JDK)**: Installed and configured in PATH.
2. **Gradle 9.5.1**: (Optional, as project includes Gradle Wrapper `./gradlew`).
3. **Python 3.14.6**: Installed at `C:\Users\dnshk\AppData\Local\Python\pythoncore-3.14-64\python.exe` (or override in `application.properties`).

---

## Setup and Installation

### 1. Install Python Dependencies
Open your shell, navigate to the `analytics` folder, and install the library requirements:
```powershell
cd analytics
& "C:\Users\dnshk\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pip install -r requirements.txt
```

### 2. Launch the Spring Boot Server
Navigate to the `backend` folder and start the development server using the Gradle wrapper:
```powershell
cd ../backend
# On Windows PowerShell
.\gradlew bootRun
```
The server will compile, copy the templates, and boot on port **8080**.

---

## Usability Guide

### 1. Navigating the Dashboard
Once the Spring Boot server has started, open your web browser and navigate to:
**[http://localhost:8080/](http://localhost:8080/)**

### 2. Configuration Settings
The sidebar controls the filters applied for the scan:
- **Min/Max Price**: Filter stocks by current price (V1 limits scan to ₹500 - ₹2,750).
- **Lookback Days**: Number of trading days studied for historical behavior (default 60).
- **Min Risk-Reward**: Shortlists only setups that exceed this R/R ratio.
- **Intraday Interval**: Candle size used for swing and time analyses (5m or 15m).

### 3. Running a Scan
1. Adjust your settings in the sidebar (for testing when moves are small, you can relax the **Min Risk-Reward Ratio** to `0.1` to force candidates like `INFY.NS` to show up).
2. Click **Run Screener**.
3. A progress spinner appears. Python fetches live data and processes calculations (takes ~4-5 seconds).
4. Results update automatically:
   - **Summary Cards**: Displays count of scanned, filtered, selected, and rejected symbols.
   - **Results Grid**: Showcases candidates that pass the filter with a classification of `TRADE` (green badge) or `WATCHLIST` (yellow badge).
   - **Download Snapshots**: Links to download `JSON` and `CSV` files become active.

### 4. Viewing Detailed Analysis
Click the **Details** button on any row in the setups table. A slide-in drawer panel overlay will open from the right side, showing:
- **Comparable Volatility statistics** (Max historical gains/losses, average extension percent).
- **Intraday pattern label and timing** (typical high/low times, swing support).
- **Detailed Execution plan** (Stop-loss levels, conservative target range, expected exit zones, risk amount, reward amount).
- **Detailed decision notes** explaining exactly why the stock was chosen or placed on a watchlist.

---

## API Endpoints Guide

If you wish to integrate StockZ with other tools, you can query these endpoints directly:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/screener/run` | Triggers a fresh live screener run with config overrides. |
| `GET` | `/api/v1/screener/latest` | Retrieves the latest successful run result as JSON. |
| `GET` | `/api/v1/screener/latest/json` | Downloads the raw `latest.json` snapshot file. |
| `GET` | `/api/v1/screener/latest/csv` | Downloads the raw `latest.csv` snapshot file. |
| `GET` | `/api/v1/screener/health` | Diagnostic status for the Java app and Python process. |

### Sample POST Request Payload:
```json
{
  "runMode": "LIVE",
  "includeTopGainers": true,
  "includeTopLosers": true,
  "snapshotMode": true,
  "outputFormats": ["JSON", "CSV"],
  "filters": {
    "minPrice": 500,
    "maxPrice": 2750
  },
  "analytics": {
    "lookbackDays": 60,
    "minRiskReward": 2.0,
    "intradayInterval": "5m"
  }
}
```
