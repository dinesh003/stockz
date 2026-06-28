import datetime

class TradeSetup:
    def __init__(self, symbol, source_list, trade_side, current_price, current_percent_move,
                 day_open=0.0, day_high=0.0, day_low=0.0):
        self.symbol = symbol
        self.source_list = source_list  # "TOP_GAINER" or "TOP_LOSER"
        self.trade_side = trade_side    # "LONG" or "SHORT"
        self.current_price = current_price
        self.current_percent_move = current_percent_move
        self.day_open = day_open
        self.day_high = day_high
        self.day_low = day_low
        
        # Screening rules
        self.price_bucket_rule = ""
        
        # Volatility / Comparable set
        self.historical_max_gain_percent = 0.0
        self.historical_max_loss_percent = 0.0
        self.comparable_sample_count = 0
        self.avg_extension_percent = 0.0
        self.avg_close_percent = 0.0
        
        # Intraday patterns
        self.typical_high_time = "N/A"
        self.typical_low_time = "N/A"
        self.time_pattern_label = "N/A"
        
        # Indicators
        self.rsi_14 = 50.0
        self.rsi_label = "NEUTRAL"
        self.bollinger_state = "INSIDE_BANDS"
        self.atr_14 = 0.0
        self.swing_stop_reference = 0.0
        
        # Risk / Reward
        self.stop_loss = 0.0
        self.stop_loss_type = "ATR"  # "ATR" or "SWING"
        self.target_min = 0.0
        self.target_max = 0.0
        self.expected_exit_zone = 0.0
        self.risk_amount = 0.0
        self.reward_amount = 0.0
        self.risk_reward_ratio = 0.0
        
        # Decisions
        self.final_decision = "REJECT"  # "TRADE", "WATCHLIST", "REJECT"
        self.decision_notes = []
        self.warnings = []

    def to_dict(self):
        """Serialize model to camelCase dictionary matching Spring Boot contract."""
        return {
            "symbol": self.symbol,
            "sourceList": self.source_list,
            "tradeSide": self.trade_side,
            "currentPrice": float(self.current_price),
            "currentPercentMove": float(self.current_percent_move),
            "dayOpen": float(self.day_open),
            "dayHigh": float(self.day_high),
            "dayLow": float(self.day_low),
            "priceBucketRule": self.price_bucket_rule,
            "historicalMaxGainPercent": float(self.historical_max_gain_percent),
            "historicalMaxLossPercent": float(self.historical_max_loss_percent),
            "comparableSampleCount": int(self.comparable_sample_count),
            "avgExtensionPercent": float(self.avg_extension_percent),
            "avgClosePercent": float(self.avg_close_percent),
            "typicalHighTime": self.typical_high_time,
            "typicalLowTime": self.typical_low_time,
            "timePatternLabel": self.time_pattern_label,
            "rsi14": float(self.rsi_14),
            "rsiLabel": self.rsi_label,
            "bollingerState": self.bollinger_state,
            "atr14": float(self.atr_14),
            "swingStopReference": float(self.swing_stop_reference),
            "stopLoss": float(self.stop_loss),
            "stopLossType": self.stop_loss_type,
            "targetMin": float(self.target_min),
            "targetMax": float(self.target_max),
            "expectedExitZone": float(self.expected_exit_zone),
            "riskAmount": float(self.risk_amount),
            "rewardAmount": float(self.reward_amount),
            "riskRewardRatio": float(self.risk_reward_ratio),
            "finalDecision": self.final_decision,
            "decisionNotes": self.decision_notes,
            "warnings": self.warnings
        }


class ScreenerRunResult:
    def __init__(self, run_id, run_time=None, config_version="v1"):
        self.run_id = run_id
        self.run_time = run_time or datetime.datetime.now().astimezone().isoformat()
        self.config_version = config_version
        self.source_status = "SUCCESS"
        self.total_scanned = 0
        self.total_filtered = 0
        self.total_selected = 0
        self.total_rejected = 0
        self.snapshot_files = {
            "json": f"/api/v1/screener/latest/json",
            "csv": f"/api/v1/screener/latest/csv"
        }
        self.setups = []

    def to_dict(self):
        """Serialize run result to camelCase matching Spring Boot contract."""
        return {
            "runId": self.run_id,
            "runTime": self.run_time,
            "configVersion": self.config_version,
            "sourceStatus": self.source_status,
            "totalScanned": int(self.total_scanned),
            "totalFiltered": int(self.total_filtered),
            "totalSelected": int(self.total_selected),
            "totalRejected": int(self.total_rejected),
            "snapshotFiles": self.snapshot_files,
            "setups": [setup.to_dict() for setup in self.setups]
        }
