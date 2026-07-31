package com.rajes.loanengine.document.dto;

import java.util.List;

/** Metadata and text lines for a single page. */
public record DocumentPage(
        int pageNumber,
        Double width,
        Double height,
        String unit,
        List<String> lines,
        int wordsCount) {}
