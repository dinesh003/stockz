package com.stockz.screener.dto;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class HealthStatusDto {
    private String springBootStatus;
    private String pythonEngineStatus;
    private String pythonVersion;
    private boolean snapshotDirectoryWritable;
}
