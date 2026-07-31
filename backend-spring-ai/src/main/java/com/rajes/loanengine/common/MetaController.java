package com.rajes.loanengine.common;

import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * Root and health endpoints the frontend polls.
 *
 * <p>Deliberately separate from Actuator's {@code /actuator/health}: the Angular client checks
 * these exact paths and bodies.
 */
@RestController
public class MetaController {

    private static final String SERVICE_NAME = "AI Loan Processing Engine";

    @GetMapping("/")
    public Map<String, String> root() {
        return Map.of("message", "Welcome to " + SERVICE_NAME, "version", "1.0.0");
    }

    @GetMapping("/health")
    public Map<String, String> health() {
        return Map.of("status", "healthy", "service", SERVICE_NAME);
    }
}
