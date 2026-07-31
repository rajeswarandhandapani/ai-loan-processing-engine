package com.rajes.loanengine.chat;

import jakarta.validation.Valid;
import java.util.Map;
import java.util.concurrent.Callable;
import org.springframework.context.annotation.Profile;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/chat")
@Profile("!ingest")
public class ChatController {

    private final ChatService chatService;

    public ChatController(ChatService chatService) {
        this.chatService = chatService;
    }

    /**
     * Handles one conversation turn.
     *
     * <p>Mapped to both {@code ""} and {@code "/"} because the existing client posts to
     * {@code /api/v1/chat/} and Spring Framework 7 no longer matches trailing slashes implicitly.
     *
     * <p>Returning a {@link Callable} hands the request to Spring MVC's async support, so
     * {@code spring.mvc.async.request-timeout} bounds the entire agent loop — however many tool
     * round trips it takes — without any threading code here.
     */
    @PostMapping({"", "/"})
    public Callable<ChatResponse> chat(@Valid @RequestBody ChatRequest request) {
        return () -> new ChatResponse(
                chatService.reply(request.message().strip(), request.sessionId().strip()),
                request.sessionId());
    }

    @GetMapping("/health")
    public Map<String, String> health() {
        return Map.of("status", "healthy", "service", "chat");
    }
}
