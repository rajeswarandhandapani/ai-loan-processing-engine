package com.rajes.loanengine.common;

import java.io.IOException;
import java.util.concurrent.TimeoutException;

/**
 * Turns low-level failures into something a loan applicant can act on.
 *
 * <p>Stack traces go to the log; the client gets a sentence.
 */
public final class FriendlyErrors {

    private FriendlyErrors() {}

    public static String describe(Throwable ex) {
        for (Throwable cause = ex; cause != null; cause = cause.getCause()) {
            if (cause instanceof TimeoutException) {
                return "The request took too long to process. Please try again.";
            }
            if (cause instanceof IOException) {
                return "Unable to reach an upstream service. Please try again shortly.";
            }
            String message = cause.getMessage();
            if (message != null) {
                String lower = message.toLowerCase();
                if (lower.contains("429") || lower.contains("rate limit")) {
                    return "Service rate limit exceeded. Please try again later.";
                }
                if (lower.contains("401") || lower.contains("unauthorized")
                        || lower.contains("invalid api key")) {
                    return "The AI service rejected our credentials. Please check the configuration.";
                }
            }
        }
        return "Something went wrong while processing your request. Please try again.";
    }
}
