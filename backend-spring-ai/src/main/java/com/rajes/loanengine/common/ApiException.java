package com.rajes.loanengine.common;

import org.springframework.http.HttpStatus;

/**
 * An error that should be reported to the client with a specific status and message.
 *
 * <p>{@link GlobalExceptionHandler} renders these as RFC 9457 {@code ProblemDetail} bodies.
 */
public class ApiException extends RuntimeException {

    private final HttpStatus status;

    public ApiException(HttpStatus status, String message) {
        super(message);
        this.status = status;
    }

    public ApiException(HttpStatus status, String message, Throwable cause) {
        super(message, cause);
        this.status = status;
    }

    public HttpStatus getStatus() {
        return status;
    }

    public static ApiException badRequest(String message) {
        return new ApiException(HttpStatus.BAD_REQUEST, message);
    }

    public static ApiException payloadTooLarge(String message) {
        return new ApiException(HttpStatus.PAYLOAD_TOO_LARGE, message);
    }
}
