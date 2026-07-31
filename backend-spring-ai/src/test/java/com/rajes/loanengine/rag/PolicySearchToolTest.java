package com.rajes.loanengine.rag;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

import java.io.File;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.ai.document.Document;
import org.springframework.ai.vectorstore.SearchRequest;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.core.io.ClassPathResource;

@ExtendWith(MockitoExtension.class)
class PolicySearchToolTest {

    @Mock
    private VectorStore vectorStore;

    private PolicySearchTool tool;

    @BeforeEach
    void setUp() {
        RagProperties properties = new RagProperties(
                new ClassPathResource("policy/lending-policy.md"),
                "Small Business Lending Policy",
                110,
                5,
                new File(".vectorstore/policy.json"));
        tool = new PolicySearchTool(vectorStore, properties);
    }

    @Test
    void mapsMatchesToTitledExcerpts() {
        when(vectorStore.similaritySearch(any(SearchRequest.class))).thenReturn(List.of(
                Document.builder()
                        .text("Minimum credit score of 650 for primary business owner")
                        .metadata(Map.of("title", "Small Business Lending Policy"))
                        .build()));

        List<PolicySearchTool.PolicyExcerpt> excerpts = tool.searchLendingPolicy("credit score");

        assertThat(excerpts).singleElement().satisfies(excerpt -> {
            assertThat(excerpt.title()).isEqualTo("Small Business Lending Policy");
            assertThat(excerpt.content()).contains("650");
        });
    }

    @Test
    void searchesWithTheConfiguredTopK() {
        when(vectorStore.similaritySearch(any(SearchRequest.class))).thenReturn(List.of());

        tool.searchLendingPolicy("collateral requirements");

        ArgumentCaptor<SearchRequest> request = ArgumentCaptor.forClass(SearchRequest.class);
        org.mockito.Mockito.verify(vectorStore).similaritySearch(request.capture());
        assertThat(request.getValue().getTopK()).isEqualTo(5);
        assertThat(request.getValue().getQuery()).isEqualTo("collateral requirements");
    }

    /** An unindexed store must read as "nothing found", not as an error. */
    @Test
    void returnsNothingWhenThePolicyHasNotBeenIndexed() {
        when(vectorStore.similaritySearch(any(SearchRequest.class))).thenReturn(List.of());

        assertThat(tool.searchLendingPolicy("interest rates")).isEmpty();
    }

    @Test
    void surfacesStoreFailuresToTheToolCallingLayer() {
        when(vectorStore.similaritySearch(any(SearchRequest.class)))
                .thenThrow(new IllegalStateException("index unavailable"));

        // Spring AI converts tool exceptions into an error message for the model by default
        // (spring.ai.tools.throw-exception-on-error=false), so the tool itself stays simple.
        assertThatThrownBy(() -> tool.searchLendingPolicy("anything"))
                .isInstanceOf(IllegalStateException.class);
    }

    @Test
    void fallsBackToTheConfiguredTitleWhenAChunkHasNoTitleMetadata() {
        when(vectorStore.similaritySearch(any(SearchRequest.class)))
                .thenReturn(List.of(Document.builder().text("some clause").build()));

        assertThat(tool.searchLendingPolicy("clause"))
                .singleElement()
                .extracting(PolicySearchTool.PolicyExcerpt::title)
                .isEqualTo("Small Business Lending Policy");
    }
}
