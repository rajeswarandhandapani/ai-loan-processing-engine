package com.rajes.loanengine.chat;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.asyncDispatch;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

@WebMvcTest(ChatController.class)
class ChatControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private ChatService chatService;

    @Test
    void returnsTheAgentReplyAndEchoesTheSession() throws Exception {
        when(chatService.reply(eq("What is the minimum credit score?"), eq("session-1")))
                .thenReturn("A minimum credit score of 650 is required.");

        MvcResult started = mockMvc.perform(post("/api/v1/chat/")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"message":"What is the minimum credit score?","session_id":"session-1"}"""))
                .andExpect(request().asyncStarted())
                .andReturn();

        mockMvc.perform(asyncDispatch(started))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.message").value("A minimum credit score of 650 is required."))
                .andExpect(jsonPath("$.session_id").value("session-1"));
    }

    /** The Angular client posts to the trailing-slash form; Framework 7 does not add it for us. */
    @Test
    void acceptsBothTrailingSlashAndBarePath() throws Exception {
        when(chatService.reply(any(), any())).thenReturn("hi");

        for (String path : new String[] {"/api/v1/chat/", "/api/v1/chat"}) {
            MvcResult started = mockMvc.perform(post(path)
                            .contentType(MediaType.APPLICATION_JSON)
                            .content("""
                                    {"message":"hello","session_id":"s"}"""))
                    .andExpect(request().asyncStarted())
                    .andReturn();
            mockMvc.perform(asyncDispatch(started)).andExpect(status().isOk());
        }
    }

    @Test
    void rejectsBlankMessageWithTheConstraintMessage() throws Exception {
        mockMvc.perform(post("/api/v1/chat/")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"message":"   ","session_id":"s"}"""))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.detail").value("Message cannot be empty"));

        verifyNoInteractions(chatService);
    }

    @Test
    void rejectsBlankSessionId() throws Exception {
        mockMvc.perform(post("/api/v1/chat/")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"message":"hello","session_id":""}"""))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.detail").value("Session ID is required"));
    }

    @Test
    void reportsAgentFailuresAsAFriendlyProblemDetail() throws Exception {
        when(chatService.reply(any(), any())).thenThrow(new RuntimeException("connection reset"));

        MvcResult started = mockMvc.perform(post("/api/v1/chat/")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"message":"hello","session_id":"s"}"""))
                .andExpect(request().asyncStarted())
                .andReturn();

        mockMvc.perform(asyncDispatch(started))
                .andExpect(status().isInternalServerError())
                .andExpect(jsonPath("$.detail").exists());
    }

    @Test
    void exposesAHealthEndpoint() throws Exception {
        mockMvc.perform(get("/api/v1/chat/health"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("healthy"))
                .andExpect(jsonPath("$.service").value("chat"));
    }

    private static org.springframework.test.web.servlet.result.RequestResultMatchers request() {
        return org.springframework.test.web.servlet.result.MockMvcResultMatchers.request();
    }
}
