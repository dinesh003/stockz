package com.stockz.screener.controller;

import com.stockz.screener.dto.HealthStatusDto;
import com.stockz.screener.dto.ScreenerResponseEnvelope;
import com.stockz.screener.dto.ScreenerResultDto;
import com.stockz.screener.dto.ScreenerRunRequest;
import com.stockz.screener.service.ScreenerService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.core.io.FileSystemResource;
import org.springframework.core.io.Resource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.io.File;

@RestController
@RequestMapping("/api/v1/screener")
@RequiredArgsConstructor
public class ScreenerController {

    private final ScreenerService screenerService;

    @PostMapping("/run")
    public ResponseEntity<ScreenerResponseEnvelope<ScreenerResultDto>> runScreener(
            @Valid @RequestBody ScreenerRunRequest request) {
        ScreenerResultDto result = screenerService.runScreener(request);
        return ResponseEntity.ok(ScreenerResponseEnvelope.success(result, "Screener run completed successfully"));
    }

    @GetMapping("/latest")
    public ResponseEntity<ScreenerResponseEnvelope<ScreenerResultDto>> getLatestResult() {
        ScreenerResultDto result = screenerService.getLatestResult();
        return ResponseEntity.ok(ScreenerResponseEnvelope.success(result, "Latest screener snapshot retrieved successfully"));
    }

    @GetMapping("/latest/json")
    public ResponseEntity<Resource> downloadLatestJson() {
        File file = screenerService.getLatestJsonFile();
        Resource resource = new FileSystemResource(file);
        
        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"latest.json\"")
                .contentType(MediaType.APPLICATION_JSON)
                .contentLength(file.length())
                .body(resource);
    }

    @GetMapping("/latest/csv")
    public ResponseEntity<Resource> downloadLatestCsv() {
        File file = screenerService.getLatestCsvFile();
        Resource resource = new FileSystemResource(file);
        
        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"latest.csv\"")
                .contentType(MediaType.parseMediaType("text/csv"))
                .contentLength(file.length())
                .body(resource);
    }

    @GetMapping("/health")
    public ResponseEntity<ScreenerResponseEnvelope<HealthStatusDto>> getHealth() {
        HealthStatusDto status = screenerService.getHealthStatus();
        return ResponseEntity.ok(ScreenerResponseEnvelope.success(status, "Python engine is reachable"));
    }
}
