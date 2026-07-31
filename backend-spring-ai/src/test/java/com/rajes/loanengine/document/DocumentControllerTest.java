package com.rajes.loanengine.document;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.multipart;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.rajes.loanengine.document.dto.DocumentAnalysis;
import com.rajes.loanengine.document.dto.DocumentField;
import com.rajes.loanengine.document.dto.DocumentPage;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.context.annotation.Import;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

@WebMvcTest(DocumentController.class)
@Import({DocumentUploadValidator.class, DocumentTypeConverter.class})
class DocumentControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private DocumentAnalysisService analysisService;

    @MockitoBean
    private SessionDocumentService sessionDocuments;

    @Test
    void listsEverySupportedDocumentType() throws Exception {
        mockMvc.perform(get("/api/v1/documents/types"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.document_types.length()").value(5))
                .andExpect(jsonPath("$.document_types[0].value").value("bank_statement"))
                .andExpect(jsonPath("$.document_types[0].name").value("BANK_STATEMENT"))
                .andExpect(jsonPath("$.document_types[4].value").value("prebuilt-layout"))
                .andExpect(jsonPath("$.document_types[4].name").value("LAYOUT"));
    }

    @Test
    void returnsTheAnalysisAsSnakeCaseJson() throws Exception {
        when(analysisService.analyze(any(), eq(DocumentType.INVOICE))).thenReturn(sampleAnalysis());

        mockMvc.perform(multipart("/api/v1/documents/upload")
                        .file(pdf())
                        .param("document_type", "invoice")
                        .param("session_id", "s-1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(true))
                .andExpect(jsonPath("$.document_type").value("invoice"))
                .andExpect(jsonPath("$.analysis.model_id").value("prebuilt-invoice"))
                .andExpect(jsonPath("$.analysis.pages[0].page_number").value(1))
                .andExpect(jsonPath("$.analysis.pages[0].words_count").value(12))
                // Azure field names are map keys, so the naming strategy must leave them alone.
                .andExpect(jsonPath("$.analysis.fields.VendorName.value").value("ACME LLC"));

        verify(sessionDocuments).add(eq("s-1"), eq("invoice.pdf"), eq("invoice"), any());
    }

    @Test
    void reportsAnalysisFailureInsideATwoHundredResponse() throws Exception {
        when(analysisService.analyze(any(), any()))
                .thenThrow(new IllegalStateException("Document Intelligence is not configured."));

        mockMvc.perform(multipart("/api/v1/documents/upload").file(pdf()))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(false))
                .andExpect(jsonPath("$.analysis").doesNotExist())
                .andExpect(jsonPath("$.error").value("Document Intelligence is not configured."));
    }

    @Test
    void rejectsUnsupportedFileTypes() throws Exception {
        mockMvc.perform(multipart("/api/v1/documents/upload")
                        .file(new MockMultipartFile("file", "notes.txt", "text/plain", "hi".getBytes())))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.detail").value(org.hamcrest.Matchers.containsString("Invalid file type")));

        verify(analysisService, never()).analyze(any(), any());
    }

    @Test
    void rejectsPdfsOverFifteenMegabytes() throws Exception {
        MockMultipartFile huge =
                new MockMultipartFile("file", "big.pdf", "application/pdf", new byte[16 * 1024 * 1024]);

        mockMvc.perform(multipart("/api/v1/documents/upload").file(huge))
                .andExpect(status().isPayloadTooLarge())
                .andExpect(jsonPath("$.detail").value("PDF file size (16.0MB) exceeds 15MB"));
    }

    @Test
    void skipsTheSessionStoreWhenNoSessionIsGiven() throws Exception {
        when(analysisService.analyze(any(), any())).thenReturn(sampleAnalysis());

        mockMvc.perform(multipart("/api/v1/documents/upload").file(pdf()))
                .andExpect(status().isOk());

        verify(sessionDocuments, never()).add(any(), any(), any(), any());
    }

    private static MockMultipartFile pdf() {
        return new MockMultipartFile("file", "invoice.pdf", "application/pdf", "%PDF-1.4".getBytes());
    }

    private static DocumentAnalysis sampleAnalysis() {
        return new DocumentAnalysis(
                "invoice",
                "prebuilt-invoice",
                "Invoice from ACME LLC",
                List.of(new DocumentPage(1, 8.5, 11.0, "inch", List.of("Invoice"), 12)),
                List.of(),
                Map.of("VendorName", new DocumentField("VendorName", "ACME LLC", 0.98, "string")),
                List.of());
    }
}
