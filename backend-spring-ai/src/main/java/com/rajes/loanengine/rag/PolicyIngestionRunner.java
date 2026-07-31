package com.rajes.loanengine.rag;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.ai.document.Document;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Component;

/**
 * One-off job that builds the policy index, then exits.
 *
 * <pre>
 * mvn spring-boot:run -Dspring-boot.run.profiles=ingest
 * mvn spring-boot:run -Dspring-boot.run.profiles=ingest -Dspring-boot.run.arguments=--reset
 * </pre>
 *
 * <p>The {@code ingest} profile also turns off the web server, so this never competes with a
 * running instance for port 8000.
 */
@Component
@Profile("ingest")
public class PolicyIngestionRunner implements ApplicationRunner {

    private static final Logger log = LoggerFactory.getLogger(PolicyIngestionRunner.class);
    private static final String SMOKE_TEST_QUERY = "What is the minimum credit score required?";

    private final PolicyIngestionService ingestionService;

    public PolicyIngestionRunner(PolicyIngestionService ingestionService) {
        this.ingestionService = ingestionService;
    }

    @Override
    public void run(ApplicationArguments args) {
        if (args.containsOption("reset")) {
            ingestionService.reset();
        }

        int chunks = ingestionService.ingest();
        log.info("Ingestion complete: {} chunks indexed", chunks);

        if (!args.containsOption("skip-test")) {
            for (Document match : ingestionService.smokeTest(SMOKE_TEST_QUERY)) {
                log.info("  [{}] {}", match.getId(), preview(match.getText()));
            }
        }
    }

    private static String preview(String text) {
        if (text == null) {
            return "";
        }
        String collapsed = text.replaceAll("\\s+", " ").trim();
        return collapsed.length() <= 120 ? collapsed : collapsed.substring(0, 120) + "...";
    }
}
