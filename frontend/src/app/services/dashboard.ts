import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

/**
 * TECHNICAL CONCEPT: TypeScript Interfaces
 * 
 * Interfaces define the "shape" of data - they're like contracts that ensure
 * objects have specific properties with specific types.
 * 
 * Benefits:
 * - Type safety: Catch errors at compile time
 * - IntelliSense: Get autocomplete in your IDE
 * - Documentation: Self-documenting code
 */

export interface FinancialData {
  revenue: number;
  expenses: number;
  profit: number;
  cashFlow: number;
}

export interface MonthlyData {
  month: string;
  revenue: number;
  expenses: number;
}

export interface DashboardData {
  businessName: string;
  applicantName: string;
  financialSummary: FinancialData;
  monthlyTrends: MonthlyData[];
  extractedAt: Date;
}

/**
 * TECHNICAL CONCEPT: Angular Service with Dependency Injection
 * 
 * @Injectable({ providedIn: 'root' })
 * - This decorator makes the service available throughout the app
 * - 'root' means it's a SINGLETON (only one instance exists)
 * - Angular's DI system automatically creates and injects it where needed
 * 
 * Why use services?
 * - Centralize business logic
 * - Share data between components
 * - Separate concerns (components handle UI, services handle data)
 */
@Injectable({
  providedIn: 'root',
})
export class DashboardService {
  
  /**
   * TECHNICAL CONCEPT: BehaviorSubject (RxJS)
   * 
   * BehaviorSubject is a special type of Observable that:
   * 1. Stores the current value
   * 2. Emits the current value immediately to new subscribers
   * 3. Allows you to push new values with .next()
   * 
   * Think of it as a "smart variable" that components can subscribe to.
   * When the value changes, all subscribers are automatically notified.
   * 
   * Private (_dashboardData$): Internal state management
   * Public (dashboardData$): Read-only stream for components
   */
  private _dashboardData$ = new BehaviorSubject<DashboardData | null>(null);
  public dashboardData$: Observable<DashboardData | null> = this._dashboardData$.asObservable();

  constructor() {}

  /**
   * Set dashboard data (typically called after document upload/analysis)
   * 
   * TECHNICAL CONCEPT: Method with Type Safety
   * - Parameter 'data' must match DashboardData interface
   * - TypeScript will error if you pass wrong data structure
   */
  setDashboardData(data: DashboardData): void {
    this._dashboardData$.next(data);
  }

  /**
   * Get current dashboard data synchronously
   * 
   * TECHNICAL CONCEPT: BehaviorSubject.value
   * - Returns the current value without subscribing
   * - Useful for one-time reads
   */
  getCurrentData(): DashboardData | null {
    return this._dashboardData$.value;
  }

  /**
   * Clear dashboard data (e.g., when starting a new application)
   */
  clearDashboardData(): void {
    this._dashboardData$.next(null);
  }

  /**
   * MOCK DATA for testing the dashboard
   * 
   * In a real app, this data would come from:
   * 1. Backend API after document analysis
   * 2. Azure Document Intelligence extraction
   * 3. Database queries
   * 
   * For now, we use mock data to build and test the UI
   */
  loadMockData(): void {
    const mockData: DashboardData = {
      businessName: 'Tech Solutions Inc.',
      applicantName: 'John Doe',
      financialSummary: {
        revenue: 250000,
        expenses: 180000,
        profit: 70000,
        cashFlow: 85000
      },
      monthlyTrends: [
        { month: 'Jan', revenue: 18000, expenses: 12000 },
        { month: 'Feb', revenue: 22000, expenses: 15000 },
        { month: 'Mar', revenue: 25000, expenses: 16000 },
        { month: 'Apr', revenue: 28000, expenses: 18000 },
        { month: 'May', revenue: 32000, expenses: 19000 },
        { month: 'Jun', revenue: 35000, expenses: 20000 },
        { month: 'Jul', revenue: 38000, expenses: 22000 },
        { month: 'Aug', revenue: 42000, expenses: 24000 },
        { month: 'Sep', revenue: 45000, expenses: 26000 },
        { month: 'Oct', revenue: 48000, expenses: 28000 },
        { month: 'Nov', revenue: 52000, expenses: 30000 },
        { month: 'Dec', revenue: 55000, expenses: 32000 }
      ],
      extractedAt: new Date()
    };

    this.setDashboardData(mockData);
  }

  /**
   * Parse financial data from Document Intelligence response
   * 
   * TECHNICAL CONCEPT: Data Transformation
   * - Takes raw API response
   * - Extracts relevant fields
   * - Transforms into our DashboardData structure
   * 
   * This is where you'd integrate with your actual backend API
   */
  parseDocumentAnalysis(analysis: any): DashboardData | null {
    try {
      // Example: Extract from key_value_pairs
      const kvPairs = analysis.key_value_pairs || {};
      
      return {
        businessName: kvPairs['Business Name'] || 'Unknown Business',
        applicantName: kvPairs['Applicant Name'] || 'Unknown Applicant',
        financialSummary: {
          revenue: parseFloat(kvPairs['Total Revenue']) || 0,
          expenses: parseFloat(kvPairs['Total Expenses']) || 0,
          profit: parseFloat(kvPairs['Net Profit']) || 0,
          cashFlow: parseFloat(kvPairs['Cash Flow']) || 0
        },
        monthlyTrends: this.extractMonthlyTrends(analysis),
        extractedAt: new Date()
      };
    } catch (error) {
      console.error('Error parsing document analysis:', error);
      return null;
    }
  }

  /**
   * Extract monthly trends from tables in the document
   * 
   * TECHNICAL CONCEPT: Array Mapping
   * - Takes array of table data
   * - Transforms each row into MonthlyData object
   * - Returns new array with transformed data
   */
  private extractMonthlyTrends(analysis: any): MonthlyData[] {
    // This would parse tables from Document Intelligence
    // For now, return empty array (will use mock data)
    return [];
  }
}
