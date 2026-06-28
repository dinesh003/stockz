package com.stockz.screener.dto;

import lombok.Data;
import java.util.List;
import java.util.Map;

@Data
public class ScreenerResultDto {
    private String runId;
    private String runTime;
    private String configVersion;
    private String sourceStatus;
    private int totalScanned;
    private int totalFiltered;
    private int totalSelected;
    private int totalRejected;
    private Map<String, String> snapshotFiles;
    private List<TradeSetupDto> setups;
}
