package com.rajes.loanengine.document;

import com.azure.ai.documentintelligence.DocumentIntelligenceClient;
import com.azure.ai.documentintelligence.DocumentIntelligenceClientBuilder;
import com.azure.ai.documentintelligence.models.AnalyzeDocumentOptions;
import com.azure.ai.documentintelligence.models.AnalyzeResult;
import com.azure.ai.documentintelligence.models.AnalyzedDocument;
import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.exception.HttpResponseException;
import com.rajes.loanengine.config.AzureProperties;
import com.rajes.loanengine.document.dto.DocumentAnalysis;
import com.rajes.loanengine.document.dto.DocumentField;
import com.rajes.loanengine.document.dto.DocumentPage;
import com.rajes.loanengine.document.dto.DocumentTable;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

/**
 * Runs an uploaded file through Azure Document Intelligence and flattens the SDK result into the
 * shape the API returns.
 *
 * <p>The client is built on first use rather than at startup, because its builder validates the
 * endpoint URL — constructing it eagerly would stop the whole application from starting when
 * Document Intelligence has not been configured yet.
 */
@Service
public class DocumentAnalysisService {

    private static final Logger log = LoggerFactory.getLogger(DocumentAnalysisService.class);

    private final AzureProperties.Credentials credentials;
    private volatile DocumentIntelligenceClient client;

    public DocumentAnalysisService(AzureProperties properties) {
        this.credentials = properties.documentIntelligence();
    }

    public DocumentAnalysis analyze(byte[] content, DocumentType documentType) {
        String modelId = documentType.getAzureModelId();
        log.info("Analyzing document with model {}", modelId);

        AnalyzeResult result;
        try {
            result = client()
                    .beginAnalyzeDocument(modelId, new AnalyzeDocumentOptions(content))
                    .getFinalResult();
        } catch (HttpResponseException ex) {
            int status = ex.getResponse() == null ? 0 : ex.getResponse().getStatusCode();
            if (status == 429) {
                throw new IllegalStateException("Service rate limit exceeded. Please try again later.", ex);
            }
            throw new IllegalStateException("Document Intelligence error: " + ex.getMessage(), ex);
        }

        Map<String, DocumentField> fields = new LinkedHashMap<>();
        List<Map<String, Object>> documents = extractDocuments(result, fields);

        return new DocumentAnalysis(
                documentType.getValue(),
                modelId,
                result.getContent(),
                extractPages(result),
                extractTables(result),
                fields,
                documents);
    }

    private DocumentIntelligenceClient client() {
        DocumentIntelligenceClient existing = client;
        if (existing != null) {
            return existing;
        }
        synchronized (this) {
            if (client == null) {
                if (!credentials.isConfigured()) {
                    throw new IllegalStateException(
                            "Document Intelligence is not configured. Set "
                                    + "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT and "
                                    + "AZURE_DOCUMENT_INTELLIGENCE_KEY.");
                }
                client = new DocumentIntelligenceClientBuilder()
                        .endpoint(credentials.endpoint())
                        .credential(new AzureKeyCredential(credentials.key()))
                        .buildClient();
            }
            return client;
        }
    }

    private static List<DocumentPage> extractPages(AnalyzeResult result) {
        List<DocumentPage> pages = new ArrayList<>();
        for (var page : nullSafe(result.getPages())) {
            List<String> lines = nullSafe(page.getLines()).stream()
                    .map(line -> line.getContent())
                    .filter(Objects::nonNull)
                    .toList();
            pages.add(new DocumentPage(
                    page.getPageNumber(),
                    page.getWidth(),
                    page.getHeight(),
                    page.getUnit() == null ? null : page.getUnit().toString(),
                    lines,
                    nullSafe(page.getWords()).size()));
        }
        return pages;
    }

    private static List<DocumentTable> extractTables(AnalyzeResult result) {
        List<DocumentTable> tables = new ArrayList<>();
        for (var table : nullSafe(result.getTables())) {
            List<Map<String, Object>> cells = nullSafe(table.getCells()).stream()
                    .map(cell -> {
                        Map<String, Object> entry = new LinkedHashMap<>();
                        entry.put("row_index", cell.getRowIndex());
                        entry.put("column_index", cell.getColumnIndex());
                        entry.put("content", cell.getContent());
                        entry.put("kind", cell.getKind() == null ? null : cell.getKind().toString());
                        return entry;
                    })
                    .toList();
            tables.add(new DocumentTable(table.getRowCount(), table.getColumnCount(), cells));
        }
        return tables;
    }

    /** Flattens per-document fields into one map, and also keeps the per-document grouping. */
    private static List<Map<String, Object>> extractDocuments(
            AnalyzeResult result, Map<String, DocumentField> flattened) {
        List<Map<String, Object>> documents = new ArrayList<>();
        for (AnalyzedDocument document : nullSafe(result.getDocuments())) {
            Map<String, Object> documentFields = new LinkedHashMap<>();
            for (var entry : nullSafe(document.getFields()).entrySet()) {
                DocumentField field = toField(entry.getKey(), entry.getValue());
                flattened.put(entry.getKey(), field);
                documentFields.put(entry.getKey(), Map.of(
                        "value", String.valueOf(field.value()),
                        "confidence", String.valueOf(field.confidence()),
                        "value_type", String.valueOf(field.valueType())));
            }
            Map<String, Object> info = new LinkedHashMap<>();
            info.put("doc_type", document.getDocumentType());
            info.put("confidence", document.getConfidence());
            info.put("fields", documentFields);
            documents.add(info);
        }
        return documents;
    }

    private static DocumentField toField(
            String name, com.azure.ai.documentintelligence.models.DocumentField field) {
        if (field == null) {
            return new DocumentField(name, null, null, null);
        }
        String type = field.getType() == null ? null : field.getType().toString();
        return new DocumentField(name, extractValue(field), field.getConfidence(), type);
    }

    private static Object extractValue(com.azure.ai.documentintelligence.models.DocumentField field) {
        if (field.getValueString() != null) {
            return field.getValueString();
        }
        if (field.getValueNumber() != null) {
            return field.getValueNumber();
        }
        if (field.getValueInteger() != null) {
            return field.getValueInteger();
        }
        if (field.getValueDate() != null) {
            return field.getValueDate().toString();
        }
        if (field.getValueCurrency() != null) {
            var currency = field.getValueCurrency();
            Map<String, Object> value = new LinkedHashMap<>();
            value.put("amount", currency.getAmount());
            value.put("currency_code", currency.getCurrencyCode());
            return value;
        }
        if (field.getValueAddress() != null) {
            var address = field.getValueAddress();
            Map<String, Object> value = new LinkedHashMap<>();
            value.put("street", address.getStreetAddress());
            value.put("city", address.getCity());
            value.put("state", address.getState());
            value.put("postal_code", address.getPostalCode());
            return value;
        }
        return field.getContent();
    }

    private static <T> List<T> nullSafe(List<T> list) {
        return list == null ? List.of() : list;
    }

    private static <K, V> Map<K, V> nullSafe(Map<K, V> map) {
        return map == null ? Map.of() : map;
    }
}
