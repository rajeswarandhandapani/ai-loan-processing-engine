import { Routes } from '@angular/router';
import { LoanApplicationComponent } from './features/loan-application/loan-application.component';

export const routes: Routes = [
  { path: '', redirectTo: '/loan-application', pathMatch: 'full' },
  { path: 'loan-application', component: LoanApplicationComponent }
];
