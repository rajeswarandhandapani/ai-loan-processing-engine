import { Routes } from '@angular/router';
import { LoanApplicationComponent } from './features/loan-application/loan-application.component';
import { Dashboard } from './features/dashboard/dashboard';

/**
 * TECHNICAL CONCEPT: Angular Routing
 * 
 * Routes define the navigation structure of your application.
 * Each route maps a URL path to a component.
 * 
 * Route Properties:
 * - path: URL segment (e.g., 'dashboard' -> /dashboard)
 * - component: Component to display when path matches
 * - redirectTo: Redirect to another path
 * - pathMatch: 'full' = exact match, 'prefix' = starts with
 * 
 * How it works:
 * 1. User navigates to /dashboard
 * 2. Angular Router matches the path
 * 3. Router loads and displays the Dashboard component
 * 4. <router-outlet> in app.html is replaced with component template
 */
export const routes: Routes = [
  { path: '', redirectTo: '/loan-application', pathMatch: 'full' },
  { path: 'loan-application', component: LoanApplicationComponent },
  { path: 'dashboard', component: Dashboard }
];
