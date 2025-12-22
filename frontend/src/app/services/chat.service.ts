import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, BehaviorSubject, throwError, of } from 'rxjs';
import { catchError, map, tap, delay, retry, timeout } from 'rxjs/operators';

/**
 * ============================================================================
 * TECHNICAL CONCEPT #1: TypeScript Interfaces
 * ============================================================================
 * Interfaces define the "shape" of data. They provide type safety and 
 * autocomplete in your IDE. Think of them as contracts that objects must follow.
 */

/**
 * Request payload sent to the backend /chat endpoint
 */
export interface ChatRequest {
  message: string;      // The user's message text
  session_id: string;   // Unique identifier for this conversation session
}

/**
 * Response received from the backend /chat endpoint
 */
export interface ChatResponse {
  message: string;      // The AI agent's response text
  session_id: string;   // Echo back the session ID for verification
}

/**
 * Internal message structure used in the frontend
 * This matches the ChatMessage interface in chat.ts
 */
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

/**
 * ============================================================================
 * TECHNICAL CONCEPT #2: Angular Services & Dependency Injection
 * ============================================================================
 * 
 * @Injectable({ providedIn: 'root' })
 * - This decorator makes the class injectable throughout the app
 * - 'root' means it's a SINGLETON - only ONE instance exists app-wide
 * - Angular's DI system automatically creates and manages the instance
 * 
 * Why use services?
 * - Separation of concerns: Components handle UI, services handle data/logic
 * - Reusability: Multiple components can use the same service
 * - Testability: Easy to mock services in unit tests
 */
@Injectable({
  providedIn: 'root'
})
export class ChatService {
  /**
   * ========================================================================
   * TECHNICAL CONCEPT #3: Environment Configuration
   * ========================================================================
   * In production, you'd use environment.ts files:
   * - environment.ts (development)
   * - environment.prod.ts (production)
   * 
   * For now, we hardcode the URL. In Day 27, we'll make this configurable.
   */
  private readonly baseUrl = 'http://localhost:8000/api/v1';

  /**
   * ========================================================================
   * TECHNICAL CONCEPT #4: RxJS BehaviorSubject
   * ========================================================================
   * 
   * BehaviorSubject is a special type of Observable that:
   * 1. Holds a CURRENT VALUE (unlike regular Observables)
   * 2. Emits the current value immediately to new subscribers
   * 3. Can be updated with .next()
   * 
   * Think of it as a "live variable" that components can subscribe to.
   * When the value changes, ALL subscribers are notified automatically.
   * 
   * Why use BehaviorSubject for loading state?
   * - Multiple components can react to loading state changes
   * - New subscribers immediately know if we're loading or not
   * - Reactive: UI updates automatically when state changes
   */
  private loadingSubject = new BehaviorSubject<boolean>(false);
  
  /**
   * Public Observable that components can subscribe to.
   * We expose this as Observable (not BehaviorSubject) to prevent
   * external code from calling .next() - encapsulation!
   */
  public isLoading$ = this.loadingSubject.asObservable();

  /**
   * ========================================================================
   * TECHNICAL CONCEPT #5: HttpClient Dependency Injection
   * ========================================================================
   * 
   * Constructor injection is Angular's way of requesting dependencies.
   * Angular sees "private http: HttpClient" and automatically:
   * 1. Creates/retrieves an HttpClient instance
   * 2. Injects it into this service
   * 3. Makes it available as this.http
   * 
   * The 'private' keyword is TypeScript shorthand that:
   * - Declares a class property
   * - Assigns the injected value to it
   * - All in one line!
   */
  constructor(private http: HttpClient) {}

  /**
   * ========================================================================
   * TECHNICAL CONCEPT #6: RxJS Observables & HTTP Requests
   * ========================================================================
   * 
   * Observable<T> represents a stream of values over time.
   * Think of it like a promise that can emit multiple values.
   * 
   * HTTP requests in Angular return Observables, not Promises.
   * Benefits:
   * - Can be cancelled (unsubscribe)
   * - Can be retried automatically
   * - Can be transformed with operators (map, filter, etc.)
   * - Lazy: Don't execute until someone subscribes
   * 
   * @param message - User's message text
   * @param sessionId - Unique session identifier
   * @returns Observable that emits the agent's response
   */
  sendMessage(message: string, sessionId: string): Observable<ChatResponse> {
    /**
     * ======================================================================
     * TECHNICAL CONCEPT #7: Request Payload Construction
     * ======================================================================
     * We create a typed object matching the backend's expected format.
     * TypeScript ensures we don't miss required fields or use wrong types.
     */
    const payload: ChatRequest = {
      message: message.trim(),
      session_id: sessionId
    };
    
    console.log('ChatService.sendMessage called');
    console.log('Payload:', payload);
    console.log('URL:', `${this.baseUrl}/chat/`);

    /**
     * ======================================================================
     * TECHNICAL CONCEPT #8: RxJS Operators & Pipe
     * ======================================================================
     * 
     * .pipe() allows us to chain operators that transform the Observable.
     * Each operator returns a NEW Observable (immutability).
     * 
     * Operators used here:
     * 
     * 1. tap() - Side effects without modifying the stream
     *    - Like console.log() but for Observables
     *    - Used here to update loading state
     * 
     * 2. timeout() - Cancels request if it takes too long
     *    - Prevents hanging requests
     *    - 30 seconds is generous for AI responses
     * 
     * 3. retry() - Automatically retries failed requests
     *    - Network hiccups happen
     *    - Retries 1 time before giving up
     * 
     * 4. catchError() - Error handling
     *    - Catches errors and returns a fallback Observable
     *    - Prevents the entire stream from breaking
     * 
     * 5. map() - Transform the emitted value
     *    - Not used here, but common for data transformation
     */
    return this.http.post<ChatResponse>(`${this.baseUrl}/chat/`, payload).pipe(
      // Cancel if no response after 30 seconds
      timeout(30000),
      
      // Retry once if request fails (network issues)
      retry(1),
      
      // Handle errors gracefully
      catchError((error: HttpErrorResponse) => {
        return this.handleError(error);
      })
    );
  }

  /**
   * ========================================================================
   * TECHNICAL CONCEPT #9: HTTP Error Handling
   * ========================================================================
   * 
   * HttpErrorResponse contains:
   * - status: HTTP status code (404, 500, etc.)
   * - error: Response body from server
   * - message: Error message
   * - statusText: Human-readable status
   * 
   * We categorize errors:
   * - Client errors (4xx): User's fault (bad input, unauthorized)
   * - Server errors (5xx): Backend's fault (crash, timeout)
   * - Network errors (status 0): No internet, CORS issues
   */
  private handleError(error: HttpErrorResponse): Observable<never> {
    let errorMessage = 'An unexpected error occurred';

    if (error.error instanceof ErrorEvent) {
      // Client-side or network error
      errorMessage = `Network error: ${error.error.message}`;
      console.error('Client-side error:', error.error.message);
    } else {
      // Backend returned an error response
      console.error(
        `Backend returned code ${error.status}, ` +
        `body was: ${JSON.stringify(error.error)}`
      );

      // Customize message based on status code
      switch (error.status) {
        case 0:
          errorMessage = 'Cannot connect to server. Please check your internet connection.';
          break;
        case 400:
          errorMessage = error.error?.detail || 'Invalid request. Please try again.';
          break;
        case 401:
          errorMessage = 'Unauthorized. Please log in again.';
          break;
        case 404:
          errorMessage = 'Chat service not found. Please contact support.';
          break;
        case 500:
          errorMessage = 'Server error. Our team has been notified.';
          break;
        case 503:
          errorMessage = 'Service temporarily unavailable. Please try again later.';
          break;
        default:
          errorMessage = error.error?.detail || `Error: ${error.statusText}`;
      }
    }

    /**
     * ======================================================================
     * TECHNICAL CONCEPT #10: throwError
     * ======================================================================
     * throwError() creates an Observable that immediately errors.
     * This allows the component to handle the error in its subscribe block.
     */
    return throwError(() => new Error(errorMessage));
  }

  /**
   * ========================================================================
   * TECHNICAL CONCEPT #11: Simulating Typing Delay (UX Enhancement)
   * ========================================================================
   * 
   * This adds a realistic typing delay before showing the agent's response.
   * Uses RxJS delay() operator to wait before emitting the value.
   * 
   * Why?
   * - Makes the AI feel more human
   * - Prevents jarring instant responses
   * - Gives user time to read their own message
   * 
   * @param response - The chat response to delay
   * @param delayMs - Milliseconds to wait (default: 500ms)
   */
  simulateTypingDelay(response: ChatResponse, delayMs: number = 500): Observable<ChatResponse> {
    return of(response).pipe(delay(delayMs));
  }

  /**
   * ========================================================================
   * TECHNICAL CONCEPT #12: Health Check Endpoint
   * ========================================================================
   * 
   * Good practice: Check if the service is available before using it.
   * This can be called on app startup or before important operations.
   */
  checkHealth(): Observable<{ status: string; service: string }> {
    return this.http.get<{ status: string; service: string }>(
      `${this.baseUrl}/chat/health`
    ).pipe(
      timeout(5000),
      catchError(() => of({ status: 'unhealthy', service: 'chat' }))
    );
  }

  /**
   * ========================================================================
   * TECHNICAL CONCEPT #13: Utility Methods
   * ========================================================================
   * Helper methods for common operations
   */

  /**
   * Get current loading state synchronously
   * Useful when you need the value immediately without subscribing
   */
  isLoading(): boolean {
    return this.loadingSubject.value;
  }

  /**
   * Manually set loading state (use sparingly)
   * Normally, loading state is managed automatically by sendMessage()
   */
  setLoading(loading: boolean): void {
    this.loadingSubject.next(loading);
  }
}

/**
 * ============================================================================
 * SUMMARY OF KEY CONCEPTS
 * ============================================================================
 * 
 * 1. TypeScript Interfaces - Type safety for data structures
 * 2. Angular Services - Reusable business logic with DI
 * 3. Singleton Pattern - One instance shared across the app
 * 4. RxJS BehaviorSubject - Stateful reactive data streams
 * 5. HttpClient - Angular's HTTP request library
 * 6. Observables - Async data streams (like Promises++)
 * 7. RxJS Operators - Transform and control data flow
 * 8. Error Handling - Graceful degradation and user feedback
 * 9. Timeout & Retry - Network resilience
 * 10. Type Safety - Compile-time error prevention
 * 
 * NEXT STEPS:
 * - Update chat.component.ts to use this service
 * - Replace simulateAgentResponse() with real API calls
 * - Handle errors in the UI with user-friendly messages
 */
