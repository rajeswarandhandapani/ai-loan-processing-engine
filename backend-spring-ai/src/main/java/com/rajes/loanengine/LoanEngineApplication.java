package com.rajes.loanengine;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

/**
 * AI Loan Processing Engine — Spring Boot + Spring AI backend.
 *
 * <p>Serves the same HTTP API as the Python/FastAPI backend in {@code backend/}, so the Angular
 * frontend can talk to either one on port 8000.
 */
@SpringBootApplication
@ConfigurationPropertiesScan
public class LoanEngineApplication {

    public static void main(String[] args) {
        SpringApplication.run(LoanEngineApplication.class, args);
    }
}
