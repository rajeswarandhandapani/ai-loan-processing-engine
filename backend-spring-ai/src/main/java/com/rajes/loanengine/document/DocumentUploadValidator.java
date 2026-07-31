package com.rajes.loanengine.document;

import com.rajes.loanengine.common.ApiException;
import java.util.Set;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.multipart.MultipartFile;

/**
 * Rejects files the analyzer cannot handle, before any Azure call is billed.
 */
@Component
public class DocumentUploadValidator {

    private static final Set<String> ALLOWED_EXTENSIONS =
            Set.of("pdf", "png", "jpg", "jpeg", "tiff", "bmp");
    private static final Set<String> IMAGE_EXTENSIONS =
            Set.of("png", "jpg", "jpeg", "tiff", "bmp");

    private static final long ONE_MB = 1024L * 1024L;
    private static final long MAX_PDF_SIZE = 15 * ONE_MB;
    private static final long MAX_IMAGE_SIZE = 5 * ONE_MB;
    private static final long MAX_FILE_SIZE = 10 * ONE_MB;

    /** @return the lower-cased extension of the validated file */
    public String validate(MultipartFile file) {
        String filename = file.getOriginalFilename();
        if (!StringUtils.hasText(filename)) {
            throw ApiException.badRequest("Filename is required");
        }

        String extension = StringUtils.getFilenameExtension(filename);
        extension = extension == null ? "" : extension.toLowerCase();
        if (!ALLOWED_EXTENSIONS.contains(extension)) {
            throw ApiException.badRequest(
                    "Invalid file type. Allowed types: "
                            + ALLOWED_EXTENSIONS.stream().sorted().map(e -> "." + e).toList());
        }

        // Exactly one cap applies. Checking the generic cap as well would make the larger PDF
        // allowance unreachable, since every PDF over 10MB would fail the generic check.
        long size = file.getSize();
        if ("pdf".equals(extension)) {
            if (size > MAX_PDF_SIZE) {
                throw tooLarge("PDF file", size, MAX_PDF_SIZE);
            }
        } else if (IMAGE_EXTENSIONS.contains(extension)) {
            if (size > MAX_IMAGE_SIZE) {
                throw tooLarge("Image file", size, MAX_IMAGE_SIZE);
            }
        } else if (size > MAX_FILE_SIZE) {
            throw tooLarge("File", size, MAX_FILE_SIZE);
        }
        return extension;
    }

    private static ApiException tooLarge(String label, long size, long limit) {
        return ApiException.payloadTooLarge(
                "%s size (%.1fMB) exceeds %dMB".formatted(label, (double) size / ONE_MB, limit / ONE_MB));
    }
}
