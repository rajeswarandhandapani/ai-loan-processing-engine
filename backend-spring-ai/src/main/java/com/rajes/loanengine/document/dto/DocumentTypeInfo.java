package com.rajes.loanengine.document.dto;

import com.rajes.loanengine.document.DocumentType;

/** One entry of {@code GET /api/v1/documents/types}. */
public record DocumentTypeInfo(String value, String name, String description) {

    public static DocumentTypeInfo of(DocumentType type) {
        return new DocumentTypeInfo(type.getValue(), type.name(), type.getDescription());
    }
}
