package com.rajes.loanengine.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * Azure service credentials.
 *
 * @param documentIntelligence endpoint/key for the Document Intelligence resource
 */
@ConfigurationProperties(prefix = "app.azure")
public record AzureProperties(Credentials documentIntelligence) {

    public record Credentials(String endpoint, String key) {

        /**
         * Treats blank values and unreplaced placeholders such as {@code <your-endpoint>} as
         * missing, so misconfiguration surfaces as a clear message rather than a DNS failure.
         */
        public boolean isConfigured() {
            return hasRealValue(endpoint) && hasRealValue(key);
        }

        private static boolean hasRealValue(String value) {
            return value != null && !value.isBlank()
                    && !value.contains("<") && !value.contains(">");
        }
    }
}
