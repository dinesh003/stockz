package com.stockz.screener.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.util.ArrayList;
import java.util.List;

@Data
public class ScreenerRunRequest {
    @NotBlank(message = "runMode is required")
    private String runMode = "LIVE";

    private boolean includeTopGainers = true;
    private boolean includeTopLosers = true;
    private boolean snapshotMode = true;
    private List<String> outputFormats = List.of("JSON", "CSV");

    /**
     * Optional: When provided, skips the Nifty universe scan and analyzes only
     * these specific NSE symbols (e.g. ["HSCL.NS", "RELIANCE.NS"]).
     */
    private List<String> symbols = new ArrayList<>();

    @NotNull(message = "filters is required")
    @Valid
    private Filters filters = new Filters();

    @NotNull(message = "analytics is required")
    @Valid
    private Analytics analytics = new Analytics();

    @Data
    public static class Filters {
        @Min(value = 0, message = "minPrice must be greater than or equal to 0")
        private double minPrice = 500.0;
        
        @Min(value = 0, message = "maxPrice must be greater than or equal to 0")
        private double maxPrice = 2750.0;
        
        private double moveThreshold = 5.0;
        private double moveVariance = 3.0;
    }

    @Data
    public static class Analytics {
        @Min(value = 20, message = "lookbackDays must be at least 20")
        private int lookbackDays = 60;
        
        private int rsiPeriod = 14;
        private int bollingerPeriod = 20;
        private double bollingerStdDev = 2.0;
        private int atrPeriod = 14;
        private double atrMultiplier = 1.5;
        
        @Min(value = 0, message = "minRiskReward must be greater than 0")
        private double minRiskReward = 0.1;

        private boolean useRiskRewardFilter = true;
        
        private String intradayInterval = "5m";
    }
}
