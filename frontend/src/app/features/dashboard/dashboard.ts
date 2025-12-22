import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration } from 'chart.js';
import { Subject, takeUntil } from 'rxjs';
import { DashboardService, DashboardData } from '../../services/dashboard';

/**
 * TECHNICAL CONCEPT: Angular Component Lifecycle
 * 
 * OnInit: Called once after component is initialized
 * - Perfect for loading data, subscriptions, API calls
 * 
 * OnDestroy: Called just before component is destroyed
 * - Perfect for cleanup (unsubscribe, clear timers, etc.)
 * - Prevents memory leaks
 */

@Component({
  selector: 'app-dashboard',
  imports: [
    CommonModule,        // Provides *ngIf, *ngFor, pipes (date, currency, etc.)
    BaseChartDirective   // ng2-charts directive for rendering Chart.js charts
  ],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.scss',
})
export class Dashboard implements OnInit, OnDestroy {
  
  /**
   * TECHNICAL CONCEPT: Component Properties
   * 
   * These are the component's state variables that the template can access.
   * When these change, Angular automatically updates the view (Data Binding).
   */
  dashboardData: DashboardData | null = null;
  isLoading = true;

  /**
   * TECHNICAL CONCEPT: Subject for Unsubscription
   * 
   * Subject is like a BehaviorSubject but without initial value.
   * We use it with takeUntil() to automatically unsubscribe from observables.
   * 
   * Why? To prevent memory leaks when component is destroyed.
   * 
   * Pattern:
   * 1. Create destroy$ Subject
   * 2. Use .pipe(takeUntil(this.destroy$)) on all subscriptions
   * 3. Call destroy$.next() in ngOnDestroy()
   * 4. All subscriptions automatically unsubscribe
   */
  private destroy$ = new Subject<void>();

  /**
   * TECHNICAL CONCEPT: Chart.js Configuration
   * 
   * Chart.js uses a configuration object to define:
   * - Chart type (line, bar, pie, doughnut, etc.)
   * - Data (labels, datasets with values and styling)
   * - Options (responsive, plugins, scales, etc.)
   * 
   * ChartConfiguration<'line'> is a TypeScript generic type that ensures
   * your config matches the requirements for a line chart.
   */

  // LINE CHART: Monthly Revenue vs Expenses Trend
  public lineChartData: ChartConfiguration<'line'>['data'] = {
    labels: [],  // X-axis labels (months)
    datasets: [
      {
        data: [],  // Y-axis values (revenue)
        label: 'Revenue',
        fill: true,  // Fill area under line
        tension: 0.4,  // Curve smoothness (0 = straight, 1 = very curved)
        borderColor: 'rgb(75, 192, 192)',  // Line color
        backgroundColor: 'rgba(75, 192, 192, 0.2)',  // Fill color (semi-transparent)
        pointBackgroundColor: 'rgb(75, 192, 192)',
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: 'rgb(75, 192, 192)'
      },
      {
        data: [],
        label: 'Expenses',
        fill: true,
        tension: 0.4,
        borderColor: 'rgb(255, 99, 132)',
        backgroundColor: 'rgba(255, 99, 132, 0.2)',
        pointBackgroundColor: 'rgb(255, 99, 132)',
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: 'rgb(255, 99, 132)'
      }
    ]
  };

  public lineChartOptions: ChartConfiguration<'line'>['options'] = {
    responsive: true,  // Chart resizes with container
    maintainAspectRatio: true,  // Keep aspect ratio when resizing
    plugins: {
      legend: {
        display: true,  // Show legend (Revenue, Expenses labels)
        position: 'top'
      },
      title: {
        display: true,
        text: 'Monthly Revenue vs Expenses Trend',
        font: { size: 16 }
      }
    },
    scales: {
      y: {
        beginAtZero: true,  // Y-axis starts at 0
        ticks: {
          callback: function(value) {
            return '$' + value.toLocaleString();  // Format as currency
          }
        }
      }
    }
  };

  public lineChartType = 'line' as const;

  // BAR CHART: Financial Summary (Revenue, Expenses, Profit, Cash Flow)
  public barChartData: ChartConfiguration<'bar'>['data'] = {
    labels: ['Revenue', 'Expenses', 'Profit', 'Cash Flow'],
    datasets: [
      {
        data: [],
        label: 'Amount ($)',
        backgroundColor: [
          'rgba(75, 192, 192, 0.6)',   // Revenue - Teal
          'rgba(255, 99, 132, 0.6)',   // Expenses - Red
          'rgba(54, 162, 235, 0.6)',   // Profit - Blue
          'rgba(255, 206, 86, 0.6)'    // Cash Flow - Yellow
        ],
        borderColor: [
          'rgb(75, 192, 192)',
          'rgb(255, 99, 132)',
          'rgb(54, 162, 235)',
          'rgb(255, 206, 86)'
        ],
        borderWidth: 2
      }
    ]
  };

  public barChartOptions: ChartConfiguration<'bar'>['options'] = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: {
        display: false  // Hide legend for bar chart (labels are on X-axis)
      },
      title: {
        display: true,
        text: 'Financial Summary',
        font: { size: 16 }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          callback: function(value) {
            return '$' + value.toLocaleString();
          }
        }
      }
    }
  };

  public barChartType = 'bar' as const;

  // DOUGHNUT CHART: Revenue vs Expenses Distribution
  public doughnutChartData: ChartConfiguration<'doughnut'>['data'] = {
    labels: ['Revenue', 'Expenses'],
    datasets: [
      {
        data: [],
        backgroundColor: [
          'rgba(75, 192, 192, 0.8)',
          'rgba(255, 99, 132, 0.8)'
        ],
        borderColor: [
          'rgb(75, 192, 192)',
          'rgb(255, 99, 132)'
        ],
        borderWidth: 2
      }
    ]
  };

  public doughnutChartOptions: ChartConfiguration<'doughnut'>['options'] = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: {
        display: true,
        position: 'bottom'
      },
      title: {
        display: true,
        text: 'Revenue vs Expenses Distribution',
        font: { size: 16 }
      }
    }
  };

  public doughnutChartType = 'doughnut' as const;

  /**
   * TECHNICAL CONCEPT: Dependency Injection (Constructor)
   * 
   * Angular automatically creates and injects the DashboardService.
   * We don't use 'new DashboardService()' - Angular handles it.
   * 
   * Benefits:
   * - Loose coupling (easy to swap implementations)
   * - Testability (easy to mock services in tests)
   * - Singleton pattern (same instance across app)
   */
  constructor(private dashboardService: DashboardService) {}

  /**
   * TECHNICAL CONCEPT: ngOnInit Lifecycle Hook
   * 
   * Called once after component is created and inputs are set.
   * Perfect place to:
   * - Load initial data
   * - Set up subscriptions
   * - Initialize component state
   */
  ngOnInit(): void {
    this.loadDashboardData();
  }

  /**
   * TECHNICAL CONCEPT: ngOnDestroy Lifecycle Hook
   * 
   * Called just before Angular destroys the component.
   * Critical for cleanup to prevent memory leaks.
   */
  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Load dashboard data and update charts
   * 
   * TECHNICAL CONCEPT: Observable Subscription with takeUntil
   * 
   * .pipe(takeUntil(this.destroy$)) automatically unsubscribes when:
   * - Component is destroyed
   * - destroy$ emits a value
   * 
   * This prevents memory leaks from lingering subscriptions.
   */
  private loadDashboardData(): void {
    this.isLoading = true;

    // Load mock data for demonstration
    this.dashboardService.loadMockData();

    // Subscribe to dashboard data changes
    this.dashboardService.dashboardData$
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          if (data) {
            this.dashboardData = data;
            this.updateCharts(data);
          }
          this.isLoading = false;
        },
        error: (error) => {
          console.error('Error loading dashboard data:', error);
          this.isLoading = false;
        }
      });
  }

  /**
   * Update all charts with new data
   * 
   * TECHNICAL CONCEPT: Data Transformation for Charts
   * 
   * We transform our DashboardData into Chart.js format:
   * - Extract labels (months, categories)
   * - Extract values (revenue, expenses)
   * - Assign to chart data objects
   * 
   * Angular's change detection automatically updates the charts.
   */
  private updateCharts(data: DashboardData): void {
    // Update Line Chart (Monthly Trends)
    this.lineChartData.labels = data.monthlyTrends.map(m => m.month);
    this.lineChartData.datasets[0].data = data.monthlyTrends.map(m => m.revenue);
    this.lineChartData.datasets[1].data = data.monthlyTrends.map(m => m.expenses);

    // Update Bar Chart (Financial Summary)
    this.barChartData.datasets[0].data = [
      data.financialSummary.revenue,
      data.financialSummary.expenses,
      data.financialSummary.profit,
      data.financialSummary.cashFlow
    ];

    // Update Doughnut Chart (Revenue vs Expenses)
    this.doughnutChartData.datasets[0].data = [
      data.financialSummary.revenue,
      data.financialSummary.expenses
    ];
  }

  /**
   * Helper method to format currency
   * 
   * TECHNICAL CONCEPT: JavaScript Internationalization API
   * 
   * toLocaleString() formats numbers according to locale:
   * - Adds commas/periods as thousands separators
   * - Adds currency symbol
   * - Handles decimal places
   */
  formatCurrency(value: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  }
}
