package com.rajes.loanengine.document;

import com.fasterxml.jackson.annotation.JsonValue;
import java.util.Arrays;

/**
 * Document kinds the API accepts, each mapped to an Azure Document Intelligence prebuilt model.
 *
 * <p>The wire value ({@code bank_statement}) differs from the Java constant name
 * ({@code BANK_STATEMENT}); the API exposes both because the frontend displays the name.
 */
public enum DocumentType {

    BANK_STATEMENT("bank_statement", "prebuilt-bankStatement.us",
            "US bank statements with transaction details"),
    INVOICE("invoice", "prebuilt-invoice",
            "Invoices with line items and totals"),
    RECEIPT("receipt", "prebuilt-receipt",
            "Receipts with merchant and purchase details"),
    TAX_W2("tax_w2", "prebuilt-tax.us.w2",
            "US W-2 tax forms"),
    LAYOUT("prebuilt-layout", "prebuilt-layout",
            "General document layout extraction");

    private final String value;
    private final String azureModelId;
    private final String description;

    DocumentType(String value, String azureModelId, String description) {
        this.value = value;
        this.azureModelId = azureModelId;
        this.description = description;
    }

    @JsonValue
    public String getValue() {
        return value;
    }

    public String getAzureModelId() {
        return azureModelId;
    }

    public String getDescription() {
        return description;
    }

    /** Resolves the wire value (not the constant name) to a type, defaulting to {@link #LAYOUT}. */
    public static DocumentType fromValue(String value) {
        return Arrays.stream(values())
                .filter(type -> type.value.equalsIgnoreCase(value))
                .findFirst()
                .orElse(LAYOUT);
    }
}
