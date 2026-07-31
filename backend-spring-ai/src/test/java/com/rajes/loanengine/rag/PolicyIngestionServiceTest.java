package com.rajes.loanengine.rag;

import static org.assertj.core.api.Assertions.assertThat;

import java.io.File;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.springframework.ai.document.Document;
import org.springframework.ai.embedding.EmbeddingModel;
import org.springframework.ai.embedding.EmbeddingResponse;
import org.springframework.ai.vectorstore.SearchRequest;
import org.springframework.ai.vectorstore.SimpleVectorStore;
import org.springframework.core.io.ClassPathResource;

/**
 * Exercises the ingestion pipeline against a real {@link SimpleVectorStore}.
 *
 * <p>Uses a deterministic stub embedding model so the suite never downloads the ~90MB ONNX model
 * and never depends on a network.
 */
class PolicyIngestionServiceTest {

    @TempDir
    Path tempDir;

    @Test
    void indexesThePolicyAndPersistsIt() {
        File storeFile = tempDir.resolve("policy.json").toFile();
        SimpleVectorStore store = newStore();
        PolicyIngestionService service = new PolicyIngestionService(store, properties(storeFile));

        int chunks = service.ingest();

        assertThat(chunks).isGreaterThan(1);
        assertThat(storeFile).exists();
    }

    @Test
    void tagsEveryChunkWithTheTitleAndAStableId() {
        SimpleVectorStore store = newStore();
        new PolicyIngestionService(store, properties(tempDir.resolve("s.json").toFile())).ingest();

        List<Document> matches = store.similaritySearch(
                SearchRequest.builder().query("credit score").topK(3).build());

        assertThat(matches).isNotEmpty().allSatisfy(match -> {
            assertThat(match.getId()).startsWith("policy-chunk-");
            assertThat(match.getMetadata()).containsEntry("title", "Small Business Lending Policy");
            assertThat(match.getMetadata()).containsKey("chunk_id");
        });
    }

    /** Stable ids mean re-running ingestion refreshes chunks instead of duplicating them. */
    @Test
    void reIngestingDoesNotDuplicateChunks() {
        SimpleVectorStore store = newStore();
        RagProperties properties = properties(tempDir.resolve("s.json").toFile());
        PolicyIngestionService service = new PolicyIngestionService(store, properties);

        int first = service.ingest();
        int second = service.ingest();

        assertThat(second).isEqualTo(first);
        assertThat(store.similaritySearch(SearchRequest.builder().query("loan").topK(100).build()))
                .hasSize(first);
    }

    @Test
    void persistedVectorsSurviveAReload() {
        File storeFile = tempDir.resolve("policy.json").toFile();
        new PolicyIngestionService(newStore(), properties(storeFile)).ingest();

        SimpleVectorStore reloaded = newStore();
        reloaded.load(storeFile);

        assertThat(reloaded.similaritySearch(SearchRequest.builder().query("credit score").topK(2).build()))
                .isNotEmpty()
                .allSatisfy(match -> assertThat(match.getMetadata())
                        .containsEntry("title", "Small Business Lending Policy"));
    }

    @Test
    void resetRemovesThePersistedFile() {
        File storeFile = tempDir.resolve("policy.json").toFile();
        PolicyIngestionService service = new PolicyIngestionService(newStore(), properties(storeFile));
        service.ingest();
        assertThat(storeFile).exists();

        service.reset();

        assertThat(storeFile).doesNotExist();
    }

    private static SimpleVectorStore newStore() {
        return SimpleVectorStore.builder(new StubEmbeddingModel()).build();
    }

    private static RagProperties properties(File storeFile) {
        return new RagProperties(
                new ClassPathResource("policy/lending-policy.md"),
                "Small Business Lending Policy",
                110,
                5,
                storeFile);
    }

    /**
     * Hashes each token into a small vector. Not semantic, but deterministic and repeatable, which
     * is all the pipeline assertions need.
     */
    private static final class StubEmbeddingModel implements EmbeddingModel {

        private static final int DIMENSIONS = 32;

        @Override
        public float[] embed(Document document) {
            return embed(document.getText() == null ? "" : document.getText());
        }

        @Override
        public float[] embed(String text) {
            float[] vector = new float[DIMENSIONS];
            for (String token : text.toLowerCase().split("\\W+")) {
                if (!token.isEmpty()) {
                    vector[Math.abs(token.hashCode()) % DIMENSIONS] += 1f;
                }
            }
            double norm = 0;
            for (float value : vector) {
                norm += value * value;
            }
            norm = Math.sqrt(norm);
            if (norm > 0) {
                for (int i = 0; i < vector.length; i++) {
                    vector[i] /= (float) norm;
                }
            }
            return vector;
        }

        @Override
        public EmbeddingResponse call(org.springframework.ai.embedding.EmbeddingRequest request) {
            List<org.springframework.ai.embedding.Embedding> embeddings =
                    new java.util.ArrayList<>();
            List<String> inputs = request.getInstructions();
            for (int i = 0; i < inputs.size(); i++) {
                embeddings.add(new org.springframework.ai.embedding.Embedding(embed(inputs.get(i)), i));
            }
            return new EmbeddingResponse(embeddings);
        }

        @Override
        public int dimensions() {
            return DIMENSIONS;
        }
    }
}
