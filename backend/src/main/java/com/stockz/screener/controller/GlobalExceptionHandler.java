package com.stockz.screener.controller;

import com.stockz.screener.dto.ApiErrorDto;
import com.stockz.screener.dto.ScreenerResponseEnvelope;
import com.stockz.screener.exception.ScreenerException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.ArrayList;
import java.util.List;

@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    /**
     * Handles custom Screener business and runtime exceptions.
     */
    @ExceptionHandler(ScreenerException.class)
    public ResponseEntity<ScreenerResponseEnvelope<Void>> handleScreenerException(ScreenerException ex) {
        log.error("ScreenerException caught: {} [Code: {}]", ex.getMessage(), ex.getErrorCode());
        
        ApiErrorDto errorDto = ApiErrorDto.builder()
                .code(ex.getErrorCode())
                .title("Screener Execution Failure")
                .detail(ex.getMessage())
                .build();
                
        ScreenerResponseEnvelope<Void> envelope = ScreenerResponseEnvelope.error(List.of(errorDto), ex.getMessage());
        return ResponseEntity.status(ex.getHttpStatus()).body(envelope);
    }

    /**
     * Handles request payload validation errors (e.g. invalid bounds, negative prices).
     */
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ScreenerResponseEnvelope<Void>> handleValidationException(MethodArgumentNotValidException ex) {
        log.warn("Payload validation failed: {}", ex.getMessage());
        
        List<ApiErrorDto> errorDtos = new ArrayList<>();
        for (FieldError fieldError : ex.getBindingResult().getFieldErrors()) {
            // Check if it's filter config error
            String errorCode = "INVALID_REQUEST";
            if (fieldError.getField().startsWith("filters")) {
                errorCode = "INVALID_FILTER_CONFIGURATION";
            }
            
            errorDtos.add(ApiErrorDto.builder()
                    .code(errorCode)
                    .title("Invalid request field")
                    .detail(fieldError.getDefaultMessage())
                    .field(fieldError.getField())
                    .build());
        }

        ScreenerResponseEnvelope<Void> envelope = ScreenerResponseEnvelope.error(errorDtos, "Validation failed");
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(envelope);
    }

    /**
     * Handles missing static resources (like favicon.ico) cleanly without logging error stack traces.
     */
    @ExceptionHandler(org.springframework.web.servlet.resource.NoResourceFoundException.class)
    public ResponseEntity<Void> handleNoResourceFoundException(org.springframework.web.servlet.resource.NoResourceFoundException ex) {
        log.warn("Static resource not found: {}", ex.getMessage());
        return ResponseEntity.notFound().build();
    }

    /**
     * Handles any unhandled general runtime exceptions.
     */
    @ExceptionHandler(Exception.class)
    public ResponseEntity<ScreenerResponseEnvelope<Void>> handleGeneralException(Exception ex) {
        log.error("Unhandled exception caught", ex);
        
        ApiErrorDto errorDto = ApiErrorDto.builder()
                .code("UNEXPECTED_INTERNAL_ERROR")
                .title("Unexpected Internal Error")
                .detail("An unexpected error occurred: " + ex.getMessage())
                .build();
                
        ScreenerResponseEnvelope<Void> envelope = ScreenerResponseEnvelope.error(List.of(errorDto), "Internal server error");
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(envelope);
    }
}
