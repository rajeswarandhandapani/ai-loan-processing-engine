package com.rajes.loanengine.document;

import com.rajes.loanengine.document.dto.DocumentAnalysis;
import java.time.Instant;

/** A document a user uploaded during one chat session. */
public record SessionDocument(
        String filename, String documentType, Instant uploadedAt, DocumentAnalysis analysis) {}
