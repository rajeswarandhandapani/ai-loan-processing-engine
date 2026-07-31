package com.rajes.loanengine.document;

import static org.assertj.core.api.Assertions.assertThat;

import com.rajes.loanengine.chat.ChatService;
import com.rajes.loanengine.document.dto.DocumentAnalysis;
import com.rajes.loanengine.document.dto.DocumentField;
import com.rajes.loanengine.document.dto.DocumentPage;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.ai.chat.model.ToolContext;

class DocumentToolTest {

    private SessionDocumentService sessionDocuments;
    private DocumentTool tool;

    @BeforeEach
    void setUp() {
        sessionDocuments = new SessionDocumentService();
        tool = new DocumentTool(sessionDocuments);
    }

    @Test
    void reportsAnEmptySessionPlainly() {
        var result = tool.getUploadedDocuments(contextFor("empty-session"));

        assertThat(result.count()).isZero();
        assertThat(result.summary()).isEqualTo("No documents uploaded in this session.");
        assertThat(result.documents()).isEmpty();
    }

    @Test
    void summarizesUploadedDocumentsWithTheirKeyFields() {
        sessionDocuments.add("s-1", "acme-statement.pdf", "bank_statement", bankStatement());

        var result = tool.getUploadedDocuments(contextFor("s-1"));

        assertThat(result.count()).isEqualTo(1);
        assertThat(result.summary())
                .contains("Documents uploaded in this session (1 total):")
                .contains("acme-statement.pdf (bank statement)")
                .contains("Account Holder: ACME LLC")
                .contains("Bank: First National");

        assertThat(result.documents()).singleElement().satisfies(document -> {
            assertThat(document.filename()).isEqualTo("acme-statement.pdf");
            assertThat(document.extractedFields()).containsEntry("AccountHolderName", "ACME LLC");
            assertThat(document.pageCount()).isEqualTo(1);
            assertThat(document.fullContent()).contains("Statement");
        });
    }

    /** Sessions must not leak into one another, since the id comes from the caller. */
    @Test
    void isolatesDocumentsBySession() {
        sessionDocuments.add("s-1", "one.pdf", "invoice", bankStatement());

        assertThat(tool.getUploadedDocuments(contextFor("s-2")).count()).isZero();
        assertThat(tool.getUploadedDocuments(contextFor("s-1")).count()).isEqualTo(1);
    }

    @Test
    void omitsFieldsThatHaveNoExtractedValue() {
        DocumentAnalysis analysis = new DocumentAnalysis(
                "invoice", "prebuilt-invoice", "Invoice", List.of(), List.of(),
                Map.of("VendorName", new DocumentField("VendorName", null, null, "string")),
                List.of());
        sessionDocuments.add("s-3", "invoice.pdf", "invoice", analysis);

        var document = tool.getUploadedDocuments(contextFor("s-3")).documents().getFirst();

        assertThat(document.extractedFields()).isEmpty();
    }

    private static ToolContext contextFor(String sessionId) {
        return new ToolContext(Map.of(ChatService.SESSION_ID_KEY, sessionId));
    }

    private static DocumentAnalysis bankStatement() {
        return new DocumentAnalysis(
                "bank_statement",
                "prebuilt-bankStatement.us",
                "Statement for ACME LLC",
                List.of(new DocumentPage(1, 8.5, 11.0, "inch", List.of("Statement"), 40)),
                List.of(),
                Map.of(
                        "AccountHolderName", new DocumentField("AccountHolderName", "ACME LLC", 0.99, "string"),
                        "BankName", new DocumentField("BankName", "First National", 0.97, "string")),
                List.of());
    }
}
