package com.rajes.loanengine.document.dto;

/** A single extracted field, e.g. {@code VendorName} or {@code InvoiceTotal}. */
public record DocumentField(String name, Object value, Double confidence, String valueType) {}
