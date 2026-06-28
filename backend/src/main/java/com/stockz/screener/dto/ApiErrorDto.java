package com.stockz.screener.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ApiErrorDto {
    private String code;
    private String title;
    private String detail;
    private String field;
}
