package com.rajes.loanengine.chat;

import jakarta.validation.constraints.NotBlank;

/**
 * A turn in the conversation.
 *
 * @param sessionId the client-generated conversation id; also the chat-memory key
 */
public record ChatRequest(
        @NotBlank(message = "Message cannot be empty") String message,
        @NotBlank(message = "Session ID is required") String sessionId) {}
