/**
 * ============================================================================
 * Header Component - Application Navigation
 * ============================================================================
 * Displays the application header with branding and navigation.
 * 
 * Key Concepts:
 * - Layout Component: Used across all pages via AppComponent
 * - RouterLink: Angular directive for client-side navigation
 * - Standalone Component: Self-contained, no NgModule required
 * 
 * Features:
 * - Application logo/branding
 * - Navigation links (if needed)
 * - Consistent header across all routes
 */

import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

/**
 * ============================================================================
 * Header Component
 * ============================================================================
 * A simple presentational component for the application header.
 * 
 * RouterLink enables:
 * - Client-side navigation (no page reload)
 * - Active link styling with routerLinkActive
 * - Query parameter handling
 */
@Component({
  selector: 'app-header',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './header.html',
  styleUrl: './header.scss'
})
export class HeaderComponent {
  // Currently no logic needed - purely presentational
  // Future: Add user menu, theme toggle, etc.
}
