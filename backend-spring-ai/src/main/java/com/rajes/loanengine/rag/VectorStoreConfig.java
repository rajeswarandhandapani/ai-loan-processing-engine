package com.rajes.loanengine.rag;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.ai.embedding.EmbeddingModel;
import org.springframework.ai.vectorstore.SimpleVectorStore;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * The only hand-written bean in the application.
 *
 * <p>Every other Spring AI component — chat model, embedding model, chat memory, the tool-calling
 * advisor, and the Azure AI Search store — is auto-configured. {@code SimpleVectorStore} has no
 * starter, so it is built here.
 *
 * <p>Setting {@code spring.ai.vectorstore.type=azure} switches off this bean and hands over to
 * {@code AzureVectorStoreAutoConfiguration} with no code change. That auto-configuration is
 * {@code matchIfMissing=true}, which is why {@code application.yml} always states the type
 * explicitly rather than relying on a default.
 */
@Configuration
public class VectorStoreConfig {

    private static final Logger log = LoggerFactory.getLogger(VectorStoreConfig.class);

    @Bean
    @ConditionalOnProperty(name = "spring.ai.vectorstore.type", havingValue = "simple",
            matchIfMissing = true)
    SimpleVectorStore simpleVectorStore(EmbeddingModel embeddingModel, RagProperties properties) {
        SimpleVectorStore store = SimpleVectorStore.builder(embeddingModel).build();

        var file = properties.storeFile();
        if (file != null && file.exists()) {
            store.load(file);
            log.info("Loaded persisted policy vectors from {}", file.getAbsolutePath());
        } else {
            log.info("No persisted vectors at {} - run with the 'ingest' profile to build them",
                    file == null ? "(unset)" : file.getAbsolutePath());
        }
        return store;
    }
}
