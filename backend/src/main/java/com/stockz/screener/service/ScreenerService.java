package com.stockz.screener.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.stockz.screener.dto.HealthStatusDto;
import com.stockz.screener.dto.ScreenerResultDto;
import com.stockz.screener.dto.ScreenerRunRequest;
import com.stockz.screener.exception.ScreenerException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;

@Slf4j
@Service
@RequiredArgsConstructor
public class ScreenerService {

    @Value("${python.executable}")
    private String pythonExecutable;

    @Value("${python.script-path}")
    private String pythonScriptPath;

    @Value("${screener.snapshot-dir}")
    private String snapshotDir;

    private final ObjectMapper objectMapper;

    /**
     * Executes the Python screener script synchronously as a subprocess.
     * Parses the JSON output and returns the result.
     */
    public ScreenerResultDto runScreener(ScreenerRunRequest request) {
        log.info("Triggering screener run: {}", request);
        
        // 1. Resolve absolute script file path
        File scriptFile = new File(pythonScriptPath);
        if (!scriptFile.isAbsolute()) {
            scriptFile = new File(System.getProperty("user.dir"), pythonScriptPath);
        }
        
        if (!scriptFile.exists()) {
            throw new ScreenerException("PYTHON_ENGINE_UNAVAILABLE", 
                    "Python script not found at absolute path: " + scriptFile.getAbsolutePath(), 503);
        }

        // 2. Prepare execution arguments
        String runId = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMddHHmmss"));
        List<String> command = new ArrayList<>();
        command.add(pythonExecutable);
        command.add(scriptFile.getAbsolutePath());
        command.add("--runId");
        command.add(runId);
        
        // Overrides
        if (request.getFilters() != null) {
            command.add("--minPrice");
            command.add(String.valueOf(request.getFilters().getMinPrice()));
            command.add("--maxPrice");
            command.add(String.valueOf(request.getFilters().getMaxPrice()));
            command.add("--moveThreshold");
            command.add(String.valueOf(request.getFilters().getMoveThreshold()));
            command.add("--moveVariance");
            command.add(String.valueOf(request.getFilters().getMoveVariance()));
        }
        
        if (request.getAnalytics() != null) {
            command.add("--lookbackDays");
            command.add(String.valueOf(request.getAnalytics().getLookbackDays()));
            command.add("--minRiskReward");
            command.add(String.valueOf(request.getAnalytics().getMinRiskReward()));
            command.add("--useRiskRewardFilter");
            command.add(String.valueOf(request.getAnalytics().isUseRiskRewardFilter()));
            command.add("--intradayInterval");
            command.add(request.getAnalytics().getIntradayInterval());
        }

        // Custom symbol mode: pass comma-separated list of NSE symbols
        if (request.getSymbols() != null && !request.getSymbols().isEmpty()) {
            command.add("--symbols");
            command.add(String.join(",", request.getSymbols()));
        }

        log.info("Launching subprocess command: {}", String.join(" ", command));

        // 3. Launch process
        ProcessBuilder pb = new ProcessBuilder(command);
        pb.directory(scriptFile.getParentFile()); // Set working directory to analytics folder
        pb.redirectErrorStream(true); // Redirect stderr to stdout to capture everything

        StringBuilder consoleOutput = new StringBuilder();
        StringBuilder jsonBuilder = new StringBuilder();
        boolean isCaptureJson = false;

        try {
            Process process = pb.start();
            
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    consoleOutput.append(line).append("\n");
                    if (line.trim().equals("---JSON_OUTPUT_START---")) {
                        isCaptureJson = true;
                        continue;
                    }
                    if (line.trim().equals("---JSON_OUTPUT_END---")) {
                        isCaptureJson = false;
                        continue;
                    }
                    if (isCaptureJson) {
                        jsonBuilder.append(line);
                    }
                }
            }

            int exitCode = process.waitFor();
            log.info("Python subprocess finished with exit code: {}", exitCode);

            if (exitCode != 0 || jsonBuilder.length() == 0) {
                log.error("Python engine failure console output:\n{}", consoleOutput);
                throw new ScreenerException("UNEXPECTED_INTERNAL_ERROR", 
                        "Python engine failed with exit code: " + exitCode + ". Console output: " + consoleOutput, 500);
            }

            // 4. Parse JSON result
            return objectMapper.readValue(jsonBuilder.toString(), ScreenerResultDto.class);

        } catch (IOException e) {
            log.error("IOException while running Python process", e);
            throw new ScreenerException("PYTHON_ENGINE_UNAVAILABLE", 
                    "Failed to launch Python engine: " + e.getMessage(), 503, e);
        } catch (InterruptedException e) {
            log.error("Python process execution was interrupted", e);
            Thread.currentThread().interrupt();
            throw new ScreenerException("UNEXPECTED_INTERNAL_ERROR", 
                    "Process execution interrupted: " + e.getMessage(), 500, e);
        }
    }

    /**
     * Reads the latest successful snapshot JSON from the snapshot directory.
     */
    public ScreenerResultDto getLatestResult() {
        File file = getLatestJsonFile();
        try {
            return objectMapper.readValue(file, ScreenerResultDto.class);
        } catch (IOException e) {
            throw new ScreenerException("UNEXPECTED_INTERNAL_ERROR", 
                    "Failed to read latest run snapshot file: " + e.getMessage(), 500, e);
        }
    }

    /**
     * Retrieves the absolute File handle for the latest snapshot JSON.
     */
    public File getLatestJsonFile() {
        File file = new File(getResolvedSnapshotDir(), "latest.json");
        if (!file.exists()) {
            throw new ScreenerException("SNAPSHOT_EXPORT_FAILED", "No screener run has been performed yet.", 404);
        }
        return file;
    }

    /**
     * Retrieves the absolute File handle for the latest snapshot CSV.
     */
    public File getLatestCsvFile() {
        File file = new File(getResolvedSnapshotDir(), "latest.csv");
        if (!file.exists()) {
            throw new ScreenerException("SNAPSHOT_EXPORT_FAILED", "No CSV screener snapshot available.", 404);
        }
        return file;
    }

    /**
     * Diagnoses and returns status details for Spring Boot and the Python runtime.
     */
    public HealthStatusDto getHealthStatus() {
        boolean pythonOk = false;
        String pyVersion = "Unknown";
        
        // 1. Check Python executable
        try {
            ProcessBuilder pb = new ProcessBuilder(pythonExecutable, "--version");
            Process p = pb.start();
            try (BufferedReader r = new BufferedReader(new InputStreamReader(p.getInputStream()))) {
                String versionLine = r.readLine();
                if (versionLine != null) {
                    pyVersion = versionLine.trim();
                    pythonOk = true;
                }
            }
            p.waitFor();
        } catch (Exception e) {
            log.warn("Failed to check Python executable version: {}", e.getMessage());
        }

        // 2. Check snapshot directory
        boolean dirWritable = false;
        try {
            File sDir = getResolvedSnapshotDir();
            if (!sDir.exists()) {
                Files.createDirectories(sDir.toPath());
            }
            dirWritable = sDir.canWrite();
        } catch (Exception e) {
            log.warn("Snapshot directory writable check failed: {}", e.getMessage());
        }

        return HealthStatusDto.builder()
                .springBootStatus("UP")
                .pythonEngineStatus(pythonOk ? "UP" : "DOWN")
                .pythonVersion(pyVersion)
                .snapshotDirectoryWritable(dirWritable)
                .build();
    }

    /**
     * Resolves snapshot dir relative to application path.
     */
    private File getResolvedSnapshotDir() {
        File dir = new File(snapshotDir);
        if (!dir.isAbsolute()) {
            dir = new File(System.getProperty("user.dir"), snapshotDir);
        }
        if (!dir.exists()) {
            dir.mkdirs();
        }
        return dir;
    }
}
