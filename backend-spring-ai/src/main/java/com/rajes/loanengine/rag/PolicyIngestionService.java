package com.rajes.loanengine.rag;

import java.io.File;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.ai.document.Document;
import org.springframework.ai.document.DocumentReader;
import org.springframework.ai.reader.TextReader;
import org.springframework.ai.reader.pdf.PagePdfDocumentReader;
import org.springframework.ai.transformer.splitter.TokenTextSplitter;
import org.springframework.ai.vectorstore.SimpleVectorStore;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.core.io.Resource;
import org.springframework.stereotype.Service;

/**
 * Builds the searchable index: read the policy, split it, embed and store it.
 *
 * <p>This is the "write" half of RAG and runs offline via the {@code ingest} profile. The "read"
 * half is {@link PolicySearchTool}, which the agent calls during a conversation.
 *
 * <p>Chunk ids are derived from position ({@code policy-chunk-0}, ...), and
 * {@code SimpleVectorStore} stores by id, so re-running ingestion replaces chunks instead of
 * piling up duplicates.
 */
@Service
public class PolicyIngestionService {

    private static final Logger log = LoggerFactory.getLogger(PolicyIngestionService.class);

    private final VectorStore vectorStore;
    private final RagProperties properties;

    public PolicyIngestionService(VectorStore vectorStore, RagProperties properties) {
        this.vectorStore = vectorStore;
        this.properties = properties;
    }

    /** @return the number of chunks indexed */
    public int ingest() {
        Resource policy = properties.policyResource();
        log.info("Reading lending policy from {}", policy.getDescription());

        List<Document> chunks = TokenTextSplitter.builder()
                .withChunkSize(properties.chunkSize())
                .build()
                .apply(readerFor(policy).get());

        List<Document> indexed = withStableIdsAndTitle(chunks);
        vectorStore.add(indexed);
        log.info("Indexed {} policy chunks", indexed.size());

        persist();
        return indexed.size();
    }

    /** Drops previously indexed vectors so a shrinking policy cannot leave stale chunks behind. */
    public void reset() {
        File file = properties.storeFile();
        if (vectorStore instanceof SimpleVectorStore && file != null && file.exists()) {
            if (file.delete()) {
                log.info("Removed persisted vectors at {}", file.getAbsolutePath());
            }
        }
    }

    /** Sanity check that retrieval actually works after indexing. */
    public List<Document> smokeTest(String query) {
        return vectorStore.similaritySearch(
                org.springframework.ai.vectorstore.SearchRequest.builder()
                        .query(query)
                        .topK(properties.topK())
                        .build());
    }

    private List<Document> withStableIdsAndTitle(List<Document> chunks) {
        return java.util.stream.IntStream.range(0, chunks.size())
                .mapToObj(i -> {
                    Document chunk = chunks.get(i);
                    var metadata = new java.util.LinkedHashMap<>(chunk.getMetadata());
                    metadata.put("title", properties.title());
                    metadata.put("chunk_id", i);
                    return Document.builder()
                            .id("policy-chunk-" + i)
                            .text(chunk.getText())
                            .metadata(metadata)
                            .build();
                })
                .toList();
    }

    private void persist() {
        File file = properties.storeFile();
        if (!(vectorStore instanceof SimpleVectorStore simple) || file == null) {
            return;  // Azure AI Search persists server-side.
        }
        try {
            File parent = file.getAbsoluteFile().getParentFile();
            if (parent != null) {
                Files.createDirectories(parent.toPath());
            }
            simple.save(file);
            log.info("Saved policy vectors to {}", file.getAbsolutePath());
        } catch (IOException ex) {
            throw new UncheckedIOException("Could not persist the vector store", ex);
        }
    }

    private static DocumentReader readerFor(Resource resource) {
        String filename = resource.getFilename();
        boolean isPdf = filename != null && filename.toLowerCase().endsWith(".pdf");
        return isPdf ? new PagePdfDocumentReader(resource) : new TextReader(resource);
    }
}
