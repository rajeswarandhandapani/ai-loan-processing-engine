package com.rajes.loanengine.document;

import com.rajes.loanengine.common.ApiException;
import com.rajes.loanengine.document.dto.DocumentAnalysis;
import com.rajes.loanengine.document.dto.DocumentTypeInfo;
import com.rajes.loanengine.document.dto.DocumentUploadResponse;
import java.io.IOException;
import java.util.Arrays;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api/v1/documents")
public class DocumentController {

    private static final Logger log = LoggerFactory.getLogger(DocumentController.class);

    private final DocumentUploadValidator validator;
    private final DocumentAnalysisService analysisService;
    private final SessionDocumentService sessionDocuments;

    public DocumentController(
            DocumentUploadValidator validator,
            DocumentAnalysisService analysisService,
            SessionDocumentService sessionDocuments) {
        this.validator = validator;
        this.analysisService = analysisService;
        this.sessionDocuments = sessionDocuments;
    }

    /**
     * Uploads and analyzes a document, optionally attaching it to a chat session.
     *
     * <p>{@code document_type} and {@code session_id} are query parameters rather than form parts,
     * matching the existing client.
     */
    @PostMapping("/upload")
    public DocumentUploadResponse upload(
            @RequestParam("file") MultipartFile file,
            @RequestParam(name = "document_type", defaultValue = "prebuilt-layout")
                    DocumentType documentType,
            @RequestParam(name = "session_id", required = false) String sessionId) {

        validator.validate(file);
        String filename = file.getOriginalFilename();

        try {
            DocumentAnalysis analysis = analysisService.analyze(readBytes(file), documentType);

            if (sessionId != null && !sessionId.isBlank()) {
                try {
                    sessionDocuments.add(sessionId, filename, documentType.getValue(), analysis);
                } catch (RuntimeException ex) {
                    // Attaching to the session is a convenience; the analysis still succeeded.
                    log.warn("Could not attach '{}' to session {}", filename, sessionId, ex);
                }
            }
            return DocumentUploadResponse.succeeded(filename, documentType.getValue(), analysis);

        } catch (RuntimeException ex) {
            // Reported in a 200 body on purpose: the frontend shows this inline in the chat
            // rather than treating it as a failed request.
            log.error("Document analysis failed for {}", filename, ex);
            return DocumentUploadResponse.failed(filename, documentType.getValue(), ex.getMessage());
        }
    }

    @GetMapping("/types")
    public Map<String, Object> types() {
        return Map.of("document_types",
                Arrays.stream(DocumentType.values()).map(DocumentTypeInfo::of).toList());
    }

    private static byte[] readBytes(MultipartFile file) {
        try {
            return file.getBytes();
        } catch (IOException ex) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "Could not read the uploaded file", ex);
        }
    }
}
