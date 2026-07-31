package com.rajes.loanengine.document;

import com.rajes.loanengine.chat.ChatService;
import com.rajes.loanengine.document.dto.DocumentAnalysis;
import com.rajes.loanengine.document.dto.DocumentField;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.ai.chat.model.ToolContext;
import org.springframework.ai.tool.annotation.Tool;
import org.springframework.stereotype.Component;

/**
 * Lets the agent read the documents the user uploaded in this conversation.
 *
 * <p>The session id arrives through {@link ToolContext}, not as a tool argument. Spring AI hides
 * {@code ToolContext} parameters from the schema it sends the model, so the model cannot ask for
 * another user's session — it can only ever see the one the request was made under.
 */
@Component
public class DocumentTool {

    private static final Logger log = LoggerFactory.getLogger(DocumentTool.class);

    /** Fields worth surfacing in the short summary, in the order a loan officer would read them. */
    private static final Map<String, String> KEY_FIELDS = Map.of(
            "AccountHolderName", "Account Holder",
            "BankName", "Bank",
            "InvoiceTotal", "Total",
            "VendorName", "Vendor");

    private final SessionDocumentService sessionDocuments;

    public DocumentTool(SessionDocumentService sessionDocuments) {
        this.sessionDocuments = sessionDocuments;
    }

    @Tool(name = "get_uploaded_documents",
            description = """
                    Retrieve the financial documents the user uploaded in this conversation, \
                    including extracted fields such as account holder, bank name, balances, \
                    totals and vendor, plus tables and full text. \
                    Use this when assessing eligibility or when the user refers to their \
                    documents. Do not use it during the initial greeting.""")
    public UploadedDocuments getUploadedDocuments(ToolContext toolContext) {
        String sessionId = (String) toolContext.getContext().get(ChatService.SESSION_ID_KEY);
        List<SessionDocument> documents = sessionDocuments.get(sessionId);
        log.info("Agent requested session documents for {} - found {}", sessionId, documents.size());

        if (documents.isEmpty()) {
            return new UploadedDocuments(0, "No documents uploaded in this session.", List.of());
        }

        return new UploadedDocuments(
                documents.size(),
                summarize(documents),
                documents.stream().map(DocumentTool::describe).toList());
    }

    private static String summarize(List<SessionDocument> documents) {
        StringBuilder summary = new StringBuilder(
                "Documents uploaded in this session (%d total):".formatted(documents.size()));
        int index = 1;
        for (SessionDocument document : documents) {
            summary.append("\n%d. %s (%s)".formatted(
                    index++, document.filename(), readable(document.documentType())));
            String keyInfo = keyInfo(document.analysis());
            if (!keyInfo.isEmpty()) {
                summary.append("\n   - ").append(keyInfo);
            }
        }
        return summary.toString();
    }

    private static String keyInfo(DocumentAnalysis analysis) {
        if (analysis == null || analysis.fields() == null) {
            return "";
        }
        return KEY_FIELDS.entrySet().stream()
                .map(entry -> {
                    DocumentField field = analysis.fields().get(entry.getKey());
                    return field == null || field.value() == null
                            ? null
                            : entry.getValue() + ": " + field.value();
                })
                .filter(java.util.Objects::nonNull)
                .reduce((a, b) -> a + ", " + b)
                .orElse("");
    }

    private static UploadedDocument describe(SessionDocument document) {
        DocumentAnalysis analysis = document.analysis();
        Map<String, Object> extracted = new LinkedHashMap<>();
        if (analysis != null && analysis.fields() != null) {
            analysis.fields().forEach((name, field) -> {
                if (field.value() != null) {
                    extracted.put(name, field.value());
                }
            });
        }
        return new UploadedDocument(
                document.filename(),
                document.documentType(),
                document.uploadedAt().toString(),
                extracted,
                analysis == null ? null : analysis.content(),
                analysis == null || analysis.pages() == null ? 0 : analysis.pages().size());
    }

    private static String readable(String documentType) {
        return documentType == null ? "document" : documentType.replace('_', ' ');
    }

    public record UploadedDocuments(int count, String summary, List<UploadedDocument> documents) {}

    public record UploadedDocument(
            String filename,
            String documentType,
            String uploadedAt,
            Map<String, Object> extractedFields,
            String fullContent,
            int pageCount) {}
}
