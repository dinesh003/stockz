package com.stockz.screener.dto;

import lombok.Data;
import java.util.List;

@Data
public class TradeSetupDto {
    private String symbol;
    private String sourceList;
    private String tradeSide;
    private double currentPrice;
    private double currentPercentMove;
    private double dayOpen;
    private double dayHigh;
    private double dayLow;
    private String priceBucketRule;
    private double historicalMaxGainPercent;
    private double historicalMaxLossPercent;
    private int comparableSampleCount;
    private double avgExtensionPercent;
    private double avgClosePercent;
    private String typicalHighTime;
    private String typicalLowTime;
    private String timePatternLabel;
    private double rsi14;
    private String rsiLabel;
    private String bollingerState;
    private double atr14;
    private double swingStopReference;
    private double stopLoss;
    private String stopLossType;
    private double targetMin;
    private double targetMax;
    private double expectedExitZone;
    private double riskAmount;
    private double rewardAmount;
    private double riskRewardRatio;
    private String finalDecision;
    private List<String> decisionNotes;
    private List<String> warnings;
}
