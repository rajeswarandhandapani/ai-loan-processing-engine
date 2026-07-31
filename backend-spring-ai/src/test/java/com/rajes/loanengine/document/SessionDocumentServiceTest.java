package com.rajes.loanengine.document;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.rajes.loanengine.document.dto.DocumentAnalysis;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;

class SessionDocumentServiceTest {

    private final SessionDocumentService service = new SessionDocumentService();

    @Test
    void returnsAnEmptyListForAnUnknownSession() {
        assertThat(service.get("never-seen")).isEmpty();
    }

    @Test
    void keepsDocumentsInUploadOrder() {
        service.add("s", "first.pdf", "invoice", analysis());
        service.add("s", "second.pdf", "receipt", analysis());

        assertThat(service.get("s"))
                .extracting(SessionDocument::filename)
                .containsExactly("first.pdf", "second.pdf");
    }

    @Test
    void evictsTheOldestDocumentPastThePerSessionCap() {
        for (int i = 0; i < 25; i++) {
            service.add("s", "doc-" + i + ".pdf", "invoice", analysis());
        }

        List<SessionDocument> documents = service.get("s");
        assertThat(documents).hasSize(20);
        assertThat(documents.getFirst().filename()).isEqualTo("doc-5.pdf");
        assertThat(documents.getLast().filename()).isEqualTo("doc-24.pdf");
    }

    @Test
    void rejectsABlankSessionId() {
        assertThatThrownBy(() -> service.add("  ", "a.pdf", "invoice", analysis()))
                .isInstanceOf(IllegalArgumentException.class);
    }

    @Test
    void clearingOneSessionLeavesOthersIntact() {
        service.add("a", "a.pdf", "invoice", analysis());
        service.add("b", "b.pdf", "invoice", analysis());

        service.clear("a");

        assertThat(service.get("a")).isEmpty();
        assertThat(service.get("b")).hasSize(1);
    }

    private static DocumentAnalysis analysis() {
        return new DocumentAnalysis(
                "invoice", "prebuilt-invoice", "content", List.of(), List.of(), Map.of(), List.of());
    }
}
