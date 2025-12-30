/**
 * ============================================================================
 * Environment Configuration - Development
 * ============================================================================
 * Centralized configuration following Single Responsibility Principle.
 * 
 * Benefits:
 * - Single source of truth for configuration
 * - Easy to swap between environments
 * - Type-safe configuration
 */

export const environment = {
  production: false,
  
  // API Configuration
  apiBaseUrl: 'http://localhost:8000/api/v1',
  
  // Feature Flags
  features: {
    enableDebugLogs: true,
    enableMockResponses: false,
  },
  
  // Upload Configuration
  upload: {
    allowedExtensions: ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp'],
    maxPdfSizeBytes: 15 * 1024 * 1024,   // 15MB
    maxImageSizeBytes: 5 * 1024 * 1024,  // 5MB
    maxFileSizeBytes: 10 * 1024 * 1024,  // 10MB default
  },
  
  // Chat Configuration
  chat: {
    requestTimeoutMs: 30000,
    retryAttempts: 1,
    typingDelayMs: 500,
  },
};

// Type export for type safety
export type Environment = typeof environment;
