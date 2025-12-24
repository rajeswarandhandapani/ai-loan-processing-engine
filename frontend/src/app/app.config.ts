/**
 * ============================================================================
 * Application Configuration
 * ============================================================================
 * Standalone Angular application configuration (Angular 15+ approach).
 * 
 * Key Concepts:
 * - ApplicationConfig: Replaces the traditional AppModule
 * - Providers: Services and features available throughout the app
 * - Standalone Bootstrap: Modern way to configure Angular apps
 * 
 * This file is referenced in main.ts when bootstrapping the application.
 */

import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';

import { routes } from './app.routes';

/**
 * ============================================================================
 * Provider Configuration
 * ============================================================================
 * Each provider adds functionality to the application:
 * 
 * - provideBrowserGlobalErrorListeners(): Global error handling
 * - provideRouter(routes): Enable routing between pages
 * - provideHttpClient(): Enable HTTP requests to backend API
 * 
 * withInterceptorsFromDi(): Allows HTTP interceptors for:
 * - Adding auth headers to requests
 * - Handling errors globally
 * - Logging requests/responses
 * 
 * Note on Animations:
 * As of Angular v20.2, @angular/animations is deprecated.
 * Use native CSS animations with animate.enter and animate.leave instead.
 * See: https://angular.dev/guide/animations
 */
export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),  // Global error handling
    provideRouter(routes),                  // Client-side routing
    provideHttpClient(withInterceptorsFromDi())  // HTTP client with interceptors
  ]
};
