package com.rajes.loanengine.document.dto;

import java.util.List;
import java.util.Map;

/** Everything extracted from one document. */
public record DocumentAnalysis(
        String documentType,
        String modelId,
        String content,
        List<DocumentPage> pages,
        List<DocumentTable> tables,
        Map<String, DocumentField> fields,
        List<Map<String, Object>> documents) {}
