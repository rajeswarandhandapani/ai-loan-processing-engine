package com.rajes.loanengine.document.dto;

import java.util.List;
import java.util.Map;

/**
 * An extracted table, e.g. the transaction rows of a bank statement.
 *
 * <p>Cell keys are already snake_case and are map entries, so Jackson's naming strategy leaves
 * them alone.
 */
public record DocumentTable(int rowCount, int columnCount, List<Map<String, Object>> cells) {}
