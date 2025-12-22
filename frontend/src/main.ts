import { bootstrapApplication } from '@angular/platform-browser';
import { appConfig } from './app/app.config';
import { App } from './app/app';

/**
 * TECHNICAL CONCEPT: Chart.js Registration
 * 
 * Chart.js v4+ uses a modular architecture with tree-shaking support.
 * You must register the components you want to use.
 * 
 * Why?
 * - Reduces bundle size (only include what you use)
 * - Better performance
 * - More control over features
 * 
 * Common components:
 * - Chart types: LineController, BarController, DoughnutController, etc.
 * - Elements: LineElement, BarElement, PointElement, ArcElement
 * - Scales: CategoryScale, LinearScale, TimeScale
 * - Plugins: Title, Tooltip, Legend, Filler
 * 
 * Registration must happen BEFORE Angular bootstraps.
 */
import {
  Chart,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  LineController,
  BarController,
  DoughnutController
} from 'chart.js';

// Register Chart.js components globally
Chart.register(
  // Controllers (required for each chart type)
  LineController,      // Line chart controller
  BarController,       // Bar chart controller
  DoughnutController,  // Doughnut/Pie chart controller
  
  // Scales
  CategoryScale,   // X-axis for categorical data (months, categories)
  LinearScale,     // Y-axis for numerical data (revenue, expenses)
  
  // Elements
  PointElement,    // Points on line charts
  LineElement,     // Lines connecting points
  BarElement,      // Bars in bar charts
  ArcElement,      // Arcs in pie/doughnut charts
  
  // Plugins
  Title,           // Chart title plugin
  Tooltip,         // Hover tooltips plugin
  Legend,          // Chart legend plugin
  Filler           // Fill area under line charts
);

bootstrapApplication(App, appConfig)
  .catch((err) => console.error(err));
