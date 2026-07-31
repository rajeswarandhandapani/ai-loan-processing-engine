package com.rajes.loanengine.chat;

import static org.assertj.core.api.Assertions.assertThat;

import com.rajes.loanengine.document.DocumentTool;
import com.rajes.loanengine.document.SessionDocumentService;
import com.rajes.loanengine.rag.PolicySearchTool;
import com.rajes.loanengine.rag.RagProperties;
import java.io.File;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.memory.ChatMemory;
import org.springframework.ai.chat.memory.InMemoryChatMemoryRepository;
import org.springframework.ai.chat.memory.MessageWindowChatMemory;
import org.springframework.ai.chat.messages.AssistantMessage;
import org.springframework.ai.chat.messages.Message;
import org.springframework.ai.chat.messages.MessageType;
import org.springframework.ai.chat.model.ChatModel;
import org.springframework.ai.chat.model.ChatResponse;
import org.springframework.ai.chat.model.Generation;
import org.springframework.ai.chat.prompt.Prompt;
import org.springframework.core.io.ClassPathResource;

/**
 * Verifies the agent wiring without calling a model: a stub {@link ChatModel} records what it was
 * asked, so the system prompt and conversation memory can be asserted directly.
 */
class ChatServiceTest {

    private final RecordingChatModel chatModel = new RecordingChatModel();
    private final ChatService chatService = newChatService();

    @Test
    void sendsTheLoanOfficerSystemPromptWithEveryTurn() {
        chatService.reply("Hello", "s-1");

        Message system = chatModel.lastPrompt().getInstructions().stream()
                .filter(message -> message.getMessageType() == MessageType.SYSTEM)
                .findFirst()
                .orElseThrow();

        assertThat(system.getText())
                .contains("professional loan officer assistant")
                .contains("search_lending_policy")
                .contains("get_uploaded_documents");
    }

    @Test
    void replaysEarlierTurnsOfTheSameConversation() {
        chatService.reply("What is the minimum credit score?", "s-1");
        chatService.reply("And what about collateral?", "s-1");

        String secondTurn = renderUserAndAssistantText(chatModel.lastPrompt());

        assertThat(secondTurn)
                .contains("What is the minimum credit score?")
                .contains("And what about collateral?");
    }

    @Test
    void keepsSeparateConversationsApart() {
        chatService.reply("I need $250,000 for expansion", "s-1");
        chatService.reply("Hello", "s-2");

        assertThat(renderUserAndAssistantText(chatModel.lastPrompt()))
                .doesNotContain("250,000")
                .contains("Hello");
    }

    @Test
    void returnsTheModelReply() {
        assertThat(chatService.reply("Hello", "s-1")).isEqualTo(RecordingChatModel.REPLY);
    }

    private ChatService newChatService() {
        ChatMemory memory = MessageWindowChatMemory.builder()
                .chatMemoryRepository(new InMemoryChatMemoryRepository())
                .build();
        RagProperties ragProperties = new RagProperties(
                new ClassPathResource("policy/lending-policy.md"),
                "Small Business Lending Policy", 110, 5, new File("target/test-store.json"));

        return new ChatService(
                ChatClient.builder(chatModel),
                memory,
                new ClassPathResource("prompts/loan-officer-system-prompt.md"),
                new PolicySearchTool(new NoOpVectorStore(), ragProperties),
                new DocumentTool(new SessionDocumentService()));
    }

    private static String renderUserAndAssistantText(Prompt prompt) {
        StringBuilder text = new StringBuilder();
        for (Message message : prompt.getInstructions()) {
            if (message.getMessageType() != MessageType.SYSTEM) {
                text.append(message.getText()).append('\n');
            }
        }
        return text.toString();
    }

    /** Captures each prompt and always answers in prose, so the tool loop terminates immediately. */
    private static final class RecordingChatModel implements ChatModel {

        static final String REPLY = "How can I help with your loan today?";

        private final List<Prompt> prompts = new ArrayList<>();

        @Override
        public ChatResponse call(Prompt prompt) {
            prompts.add(prompt);
            return new ChatResponse(List.of(new Generation(new AssistantMessage(REPLY))));
        }

        Prompt lastPrompt() {
            return prompts.getLast();
        }
    }

    /** The agent never reaches retrieval in these tests; the tool just needs to be constructible. */
    private static final class NoOpVectorStore implements org.springframework.ai.vectorstore.VectorStore {

        @Override
        public void add(List<org.springframework.ai.document.Document> documents) {}

        @Override
        public void delete(List<String> idList) {}

        @Override
        public void delete(org.springframework.ai.vectorstore.filter.Filter.Expression expression) {}

        @Override
        public List<org.springframework.ai.document.Document> similaritySearch(
                org.springframework.ai.vectorstore.SearchRequest request) {
            return List.of();
        }
    }
}
