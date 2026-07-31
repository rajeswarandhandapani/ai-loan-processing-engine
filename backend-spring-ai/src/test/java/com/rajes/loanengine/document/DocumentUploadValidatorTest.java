package com.rajes.loanengine.document;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.rajes.loanengine.common.ApiException;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.springframework.http.HttpStatus;
import org.springframework.mock.web.MockMultipartFile;

class DocumentUploadValidatorTest {

    private final DocumentUploadValidator validator = new DocumentUploadValidator();

    @ParameterizedTest
    @ValueSource(strings = {"a.pdf", "a.PNG", "a.jpg", "a.jpeg", "a.tiff", "a.bmp"})
    void acceptsEverySupportedExtension(String filename) {
        assertThat(validator.validate(file(filename, 1024))).isEqualTo(
                filename.substring(filename.lastIndexOf('.') + 1).toLowerCase());
    }

    @Test
    void rejectsAMissingFilename() {
        assertThatThrownBy(() -> validator.validate(file("", 10)))
                .isInstanceOf(ApiException.class)
                .hasMessage("Filename is required");
    }

    @Test
    void rejectsUnsupportedExtensions() {
        assertThatThrownBy(() -> validator.validate(file("notes.txt", 10)))
                .isInstanceOf(ApiException.class)
                .hasMessageContaining("Invalid file type");
    }

    @Test
    void allowsAPdfUpToFifteenMegabytes() {
        assertThat(validator.validate(file("big.pdf", 15 * 1024 * 1024))).isEqualTo("pdf");
    }

    @Test
    void rejectsAPdfOverFifteenMegabytesWithTheSizeInTheMessage() {
        assertThatThrownBy(() -> validator.validate(file("big.pdf", 16 * 1024 * 1024)))
                .isInstanceOf(ApiException.class)
                .hasMessage("PDF file size (16.0MB) exceeds 15MB")
                .extracting(ex -> ((ApiException) ex).getStatus())
                .isEqualTo(HttpStatus.PAYLOAD_TOO_LARGE);
    }

    /** Images get a tighter cap than PDFs. */
    @Test
    void rejectsAnImageOverFiveMegabytes() {
        assertThatThrownBy(() -> validator.validate(file("scan.png", 6 * 1024 * 1024)))
                .isInstanceOf(ApiException.class)
                .hasMessage("Image file size (6.0MB) exceeds 5MB");
    }

    private static MockMultipartFile file(String filename, int size) {
        return new MockMultipartFile("file", filename, "application/octet-stream", new byte[size]);
    }
}
