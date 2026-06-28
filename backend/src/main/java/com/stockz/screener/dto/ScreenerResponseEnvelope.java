package com.stockz.screener.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ScreenerResponseEnvelope<T> {
    private String status;
    private String message;
    private String timestamp;
    private String requestId;
    private T data;
    
    @Builder.Default
    private List<ApiErrorDto> errors = new ArrayList<>();

    public static <T> ScreenerResponseEnvelope<T> success(T data, String message) {
        return ScreenerResponseEnvelope.<T>builder()
                .status("SUCCESS")
                .message(message)
                .timestamp(ZonedDateTime.now().format(DateTimeFormatter.ISO_OFFSET_DATE_TIME))
                .requestId(UUID.randomUUID().toString())
                .data(data)
                .build();
    }

    public static <T> ScreenerResponseEnvelope<T> error(List<ApiErrorDto> errors, String message) {
        return ScreenerResponseEnvelope.<T>builder()
                .status("ERROR")
                .message(message)
                .timestamp(ZonedDateTime.now().format(DateTimeFormatter.ISO_OFFSET_DATE_TIME))
                .requestId(UUID.randomUUID().toString())
                .data(null)
                .errors(errors)
                .build();
    }
}
