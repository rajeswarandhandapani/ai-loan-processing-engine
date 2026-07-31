package com.rajes.loanengine.document;

import com.github.benmanes.caffeine.cache.Cache;
import com.github.benmanes.caffeine.cache.Caffeine;
import com.rajes.loanengine.document.dto.DocumentAnalysis;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.CopyOnWriteArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

/**
 * Holds documents uploaded during a chat session so the agent can reason about them.
 *
 * <p>In-process and non-persistent, with a TTL so abandoned sessions release memory. Swap the
 * Caffeine cache for Redis to run more than one instance.
 */
@Service
public class SessionDocumentService {

    private static final Logger log = LoggerFactory.getLogger(SessionDocumentService.class);
    private static final int MAX_DOCUMENTS_PER_SESSION = 20;

    private final Cache<String, List<SessionDocument>> sessions = Caffeine.newBuilder()
            .expireAfterAccess(Duration.ofHours(4))
            .maximumSize(1_000)
            .build();

    public void add(String sessionId, String filename, String documentType, DocumentAnalysis analysis) {
        if (sessionId == null || sessionId.isBlank()) {
            throw new IllegalArgumentException("Session ID cannot be empty");
        }
        List<SessionDocument> documents =
                sessions.get(sessionId, key -> new CopyOnWriteArrayList<>());
        if (documents.size() >= MAX_DOCUMENTS_PER_SESSION) {
            SessionDocument evicted = documents.remove(0);
            log.info("Evicted oldest document '{}' from session {}", evicted.filename(), sessionId);
        }
        documents.add(new SessionDocument(filename, documentType, Instant.now(), analysis));
        log.info("Stored '{}' in session {} (total: {})", filename, sessionId, documents.size());
    }

    public List<SessionDocument> get(String sessionId) {
        return Optional.ofNullable(sessions.getIfPresent(sessionId)).map(List::copyOf).orElseGet(List::of);
    }

    public void clear(String sessionId) {
        sessions.invalidate(sessionId);
    }
}
