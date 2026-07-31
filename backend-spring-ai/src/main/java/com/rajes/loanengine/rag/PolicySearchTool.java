package com.rajes.loanengine.rag;

import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.ai.document.Document;
import org.springframework.ai.tool.annotation.Tool;
import org.springframework.ai.tool.annotation.ToolParam;
import org.springframework.ai.vectorstore.SearchRequest;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.stereotype.Component;

/**
 * The retrieval half of RAG, exposed as a tool so the model decides when it needs the policy.
 *
 * <p>An always-on RAG advisor would search on every turn, including greetings. Making retrieval a
 * tool lets the agent skip it when the question is not about policy, which is exactly what the
 * system prompt instructs.
 *
 * <p>The description below is part of the prompt: it is what the model reads when deciding whether
 * to call this. Keep it specific.
 */
@Component
public class PolicySearchTool {

    private static final Logger log = LoggerFactory.getLogger(PolicySearchTool.class);

    private final VectorStore vectorStore;
    private final RagProperties properties;

    public PolicySearchTool(VectorStore vectorStore, RagProperties properties) {
        this.vectorStore = vectorStore;
        this.properties = properties;
    }

    @Tool(name = "search_lending_policy",
            description = """
                    Search the official small business lending policy for eligibility criteria, \
                    credit score thresholds, required documents, loan amounts, interest rates, \
                    repayment terms, collateral rules and prohibited uses. \
                    ALWAYS use this tool for policy questions - never answer them from memory.""")
    public List<PolicyExcerpt> searchLendingPolicy(
            @ToolParam(description = "The policy question to look up") String query) {

        List<Document> matches = vectorStore.similaritySearch(
                SearchRequest.builder().query(query).topK(properties.topK()).build());

        log.info("Policy search for '{}' returned {} excerpts", query, matches.size());

        return matches.stream()
                .map(document -> new PolicyExcerpt(
                        String.valueOf(document.getMetadata().getOrDefault("title", properties.title())),
                        document.getText()))
                .toList();
    }

    /** One retrieved passage. Spring AI serializes this back to the model. */
    public record PolicyExcerpt(String title, String content) {}
}
