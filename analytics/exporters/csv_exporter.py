import csv
import os
from utils.logger import log_info, log_error

def export_to_csv(run_result, output_path):
    """
    Writes the list of TradeSetup results in ScreenerRunResult to a CSV file.
    """
    try:
        # Ensure directories exist
        dir_name = os.path.dirname(output_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
            
        headers = [
            "symbol", "tradeSide", "sourceList", "currentPrice", "currentPercentMove",
            "historicalMaxGainPercent", "historicalMaxLossPercent", "comparableSampleCount",
            "avgExtensionPercent", "avgClosePercent", "typicalHighTime", "typicalLowTime",
            "timePatternLabel", "rsi14", "rsiLabel", "bollingerState", "atr14",
            "swingStopReference", "stopLoss", "stopLossType", "targetMin", "targetMax",
            "expectedExitZone", "riskAmount", "rewardAmount", "riskRewardRatio",
            "finalDecision", "decisionNotes", "runId", "runTime"
        ]
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            
            for setup in run_result.setups:
                # Convert list of notes to a single string
                notes_str = "; ".join(setup.decision_notes)
                
                writer.writerow([
                    setup.symbol,
                    setup.trade_side,
                    setup.source_list,
                    setup.current_price,
                    setup.current_percent_move,
                    setup.historical_max_gain_percent,
                    setup.historical_max_loss_percent,
                    setup.comparable_sample_count,
                    setup.avg_extension_percent,
                    setup.avg_close_percent,
                    setup.typical_high_time,
                    setup.typical_low_time,
                    setup.time_pattern_label,
                    setup.rsi_14,
                    setup.rsi_label,
                    setup.bollinger_state,
                    setup.atr_14,
                    setup.swing_stop_reference,
                    setup.stop_loss,
                    setup.stop_loss_type,
                    setup.target_min,
                    setup.target_max,
                    setup.expected_exit_zone,
                    setup.risk_amount,
                    setup.reward_amount,
                    setup.risk_reward_ratio,
                    setup.final_decision,
                    notes_str,
                    run_result.run_id,
                    run_result.run_time
                ])
                
        log_info("CSV_EXPORT", status="SUCCESS", message=f"Exported CSV snapshot to {output_path}")
        return True
    except Exception as e:
        log_error("CSV_EXPORT", error_message=f"Failed to export CSV: {str(e)}")
        return False
