package com.rajes.loanengine.chat;

/** The assistant's reply, echoing the session it belongs to. */
public record ChatResponse(String message, String sessionId) {}
