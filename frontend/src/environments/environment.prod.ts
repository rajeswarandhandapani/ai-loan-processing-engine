/**
 * ============================================================================
 * Environment Configuration - Production
 * ============================================================================
 * Production configuration with optimized settings.
 * 
 * Note: Replace apiBaseUrl with your production API URL.
 */

export const environment = {
  production: true,
  
  // API Configuration - Update with production URL
  apiBaseUrl: 'https://api.yourdomain.com/api/v1',
  
  // Feature Flags
  features: {
    enableDebugLogs: false,
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

export type Environment = typeof environment;
