package com.rajes.loanengine.document.dto;

/**
 * Result of an upload.
 *
 * <p>Analysis failures are reported here with {@code success=false} and an HTTP 200 status, not as
 * an error response — the frontend renders the message inline in the chat instead of treating it
 * as a request failure. Validation failures (bad type, too large) still return 4xx.
 */
public record DocumentUploadResponse(
        boolean success,
        String message,
        String filename,
        String documentType,
        DocumentAnalysis analysis,
        String error) {

    public static DocumentUploadResponse succeeded(
            String filename, String documentType, DocumentAnalysis analysis) {
        return new DocumentUploadResponse(
                true, "Document analyzed successfully", filename, documentType, analysis, null);
    }

    public static DocumentUploadResponse failed(
            String filename, String documentType, String error) {
        return new DocumentUploadResponse(
                false, "Document analysis failed", filename, documentType, null, error);
    }
}
