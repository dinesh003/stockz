package com.stockz.screener.exception;

import lombok.Getter;

@Getter
public class ScreenerException extends RuntimeException {
    private final String errorCode;
    private final int httpStatus;

    public ScreenerException(String errorCode, String message, int httpStatus) {
        super(message);
        this.errorCode = errorCode;
        this.httpStatus = httpStatus;
    }

    public ScreenerException(String errorCode, String message, int httpStatus, Throwable cause) {
        super(message, cause);
        this.errorCode = errorCode;
        this.httpStatus = httpStatus;
    }
}
