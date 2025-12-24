/**
 * ============================================================================
 * Root Application Component
 * ============================================================================
 * This is the root component of the Angular application.
 * 
 * Key Concepts:
 * - Root Component: The top-level component that hosts all other components
 * - RouterOutlet: Placeholder where routed components are rendered
 * - Standalone: Angular 15+ feature - no NgModule required
 * 
 * Component Hierarchy:
 *   AppComponent (this)
 *     └── HeaderComponent (navigation)
 *     └── RouterOutlet (page content)
 *           └── HomeComponent (default route)
 *                 └── ChatComponent
 *                 └── FileUploadComponent
 */

import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { HeaderComponent } from './layout/header/header';

/**
 * ============================================================================
 * Component Decorator
 * ============================================================================
 * @Component() configures how Angular treats this class:
 * - selector: HTML tag to use this component (<app-root></app-root>)
 * - standalone: true = No NgModule needed (modern Angular approach)
 * - imports: Dependencies this component needs
 * - templateUrl: Path to HTML template
 * - styleUrls: Path to component-specific styles
 */
@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, HeaderComponent],
  templateUrl: './app.html',
  styleUrls: ['./app.scss']
})
export class AppComponent {
  /**
   * Application title displayed in the browser tab and header.
   * This property can be used in the template with {{ title }}
   */
  title = 'AI Loan Processing Engine';
}
