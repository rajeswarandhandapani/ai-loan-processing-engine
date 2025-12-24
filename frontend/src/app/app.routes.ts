/**
 * ============================================================================
 * Application Routes Configuration
 * ============================================================================
 * Defines the URL structure and navigation for the application.
 * 
 * Key Concepts:
 * - Routes: Maps URL paths to Angular components
 * - Lazy Loading: Load features on-demand (not used here for simplicity)
 * - Guards: Protect routes (e.g., authentication) - can be added later
 * 
 * Current Routes:
 * - '' (root): HomeComponent - Main chat and document upload interface
 * 
 * Future Routes (examples):
 * - '/history': Chat history page
 * - '/settings': User preferences
 * - '/admin': Admin dashboard (with auth guard)
 */

import { Routes } from '@angular/router';
import { HomeComponent } from './features/home/home.component';

/**
 * ============================================================================
 * Route Definitions
 * ============================================================================
 * Each route object defines:
 * - path: URL segment ('' = root/home)
 * - component: Component to render for this path
 * 
 * Optional properties (not used here):
 * - canActivate: Guards to check before activating route
 * - loadComponent: Lazy load component (performance optimization)
 * - children: Nested routes
 * - data: Static data passed to component
 */
export const routes: Routes = [
  { path: '', component: HomeComponent }  // Root path shows HomeComponent
];
