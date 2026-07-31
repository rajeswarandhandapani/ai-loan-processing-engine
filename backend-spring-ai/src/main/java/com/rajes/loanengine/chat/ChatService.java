package com.rajes.loanengine.chat;

import com.rajes.loanengine.document.DocumentTool;
import com.rajes.loanengine.rag.PolicySearchTool;
import java.util.Map;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.client.advisor.MessageChatMemoryAdvisor;
import org.springframework.ai.chat.memory.ChatMemory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Profile;
import org.springframework.core.io.Resource;
import org.springframework.stereotype.Service;

/**
 * The loan-officer agent.
 *
 * <p>There is no graph or state machine here. A {@link ChatClient} with tools attached <em>is</em>
 * the agent loop: Spring AI auto-registers a {@code ToolCallingAdvisor} that keeps calling the
 * model and running whichever tools it asks for until the model answers in prose. The
 * {@link ChatMemory} bean — also auto-configured — replays the earlier turns of the same session.
 *
 * <p>Everything injected below is auto-configured. The one exception in this application is the
 * {@code SimpleVectorStore} behind {@link PolicySearchTool}, which has no starter.
 *
 * <p>Excluded from the {@code ingest} profile: indexing the policy needs the embedding model but
 * no chat model, and that profile switches the chat model off.
 */
@Service
@Profile("!ingest")
public class ChatService {

    /** Key under which the session id is passed to tools without exposing it to the model. */
    public static final String SESSION_ID_KEY = "sessionId";

    private final ChatClient chatClient;
    private final PolicySearchTool policySearchTool;
    private final DocumentTool documentTool;

    public ChatService(
            ChatClient.Builder chatClientBuilder,
            ChatMemory chatMemory,
            @Value("classpath:prompts/loan-officer-system-prompt.md") Resource systemPrompt,
            PolicySearchTool policySearchTool,
            DocumentTool documentTool) {
        this.chatClient = chatClientBuilder
                .defaultSystem(systemPrompt)
                .defaultAdvisors(MessageChatMemoryAdvisor.builder(chatMemory).build())
                .build();
        this.policySearchTool = policySearchTool;
        this.documentTool = documentTool;
    }

    public String reply(String message, String sessionId) {
        return chatClient.prompt()
                .user(message)
                // Spring AI 2.0 requires the conversation id per call; there is no default.
                .advisors(advisor -> advisor.param(ChatMemory.CONVERSATION_ID, sessionId))
                .tools(policySearchTool, documentTool)
                .toolContext(Map.of(SESSION_ID_KEY, sessionId))
                .call()
                .content();
    }
}
