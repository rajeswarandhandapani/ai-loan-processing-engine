package com.rajes.loanengine.rag;

import java.io.File;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.core.io.Resource;

/**
 * Knobs for the retrieval pipeline.
 *
 * @param policyResource the lending policy to index ({@code .pdf} or plain text/markdown)
 * @param title metadata attached to every chunk, shown to the model alongside the excerpt
 * @param chunkSize chunk size in <em>tokens</em> — {@code TokenTextSplitter} counts tokens, not
 *     characters
 * @param topK how many excerpts the search tool returns
 * @param storeFile where {@code SimpleVectorStore} persists its vectors between runs
 */
@ConfigurationProperties(prefix = "app.rag")
public record RagProperties(
        Resource policyResource, String title, int chunkSize, int topK, File storeFile) {}
