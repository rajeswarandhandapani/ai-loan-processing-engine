package com.rajes.loanengine.document;

import org.springframework.core.convert.converter.Converter;
import org.springframework.stereotype.Component;

/**
 * Binds the {@code document_type} query parameter by wire value rather than by enum constant name,
 * so {@code ?document_type=bank_statement} resolves instead of requiring {@code BANK_STATEMENT}.
 */
@Component
public class DocumentTypeConverter implements Converter<String, DocumentType> {

    @Override
    public DocumentType convert(String source) {
        return DocumentType.fromValue(source);
    }
}
