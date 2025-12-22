import { Component, ElementRef, ViewChild, AfterViewChecked, Output, EventEmitter, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { trigger, transition, style, animate } from '@angular/animations';
import { ChatService } from '../../services/chat.service';
import { Subscription } from 'rxjs';

/**
 * ============================================================================
 * TECHNICAL CONCEPT #1: TypeScript Interfaces
 * ============================================================================
 * Interfaces define the structure of objects. They provide:
 * - Type safety: Catch errors at compile time
 * - IntelliSense: Auto-complete in your IDE
 * - Documentation: Self-documenting code
 * 
 * This interface represents a single chat message in the conversation.
 */
export interface ChatMessage {
  id: string;                    // Unique identifier for the message
  role: 'user' | 'assistant';    // Union type: can only be 'user' OR 'assistant'
  content: string;               // The actual message text
  timestamp: Date;               // When the message was created
}

/**
 * ============================================================================
 * TECHNICAL CONCEPT #2: Angular Component Decorator
 * ============================================================================
 * @Component() is a decorator that tells Angular this is a component.
 * 
 * Key properties:
 * - selector: HTML tag name to use this component (<app-chat></app-chat>)
 * - standalone: true = No need for NgModule (Angular 15+ feature)
 * - imports: Other modules/components this component needs
 * - templateUrl: Path to the HTML template
 * - styleUrl: Path to the component-specific styles
 * - animations: Angular animations for smooth UI transitions
 */
@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chat.html',
  styleUrl: './chat.scss',
  animations: [
    /**
     * ======================================================================
     * TECHNICAL CONCEPT #3: Angular Animations
     * ======================================================================
     * trigger() creates a named animation that can be used in templates
     * :enter is a special state when an element is added to the DOM
     * 
     * This animation:
     * 1. Starts with opacity: 0 and translateY(10px) - invisible and below
     * 2. Animates to opacity: 1 and translateY(0) - visible and in place
     * 3. Takes 200ms with ease-out timing (fast start, slow end)
     */
    trigger('messageAnimation', [
      transition(':enter', [
        style({ opacity: 0, transform: 'translateY(10px)' }),
        animate('200ms ease-out', style({ opacity: 1, transform: 'translateY(0)' }))
      ])
    ])
  ]
})
/**
 * ============================================================================
 * TECHNICAL CONCEPT #4: Component Lifecycle & Interfaces
 * ============================================================================
 * 
 * AfterViewChecked: Called after Angular checks the component's view
 * - Used here for auto-scrolling after messages are rendered
 * 
 * OnDestroy: Called when the component is destroyed
 * - Used here to clean up subscriptions and prevent memory leaks
 * 
 * Why implement OnDestroy?
 * - Subscriptions keep running even after component is destroyed
 * - This causes memory leaks (app gets slower over time)
 * - Always unsubscribe in ngOnDestroy()!
 */
export class ChatComponent implements AfterViewChecked, OnDestroy {
  /**
   * ========================================================================
   * TECHNICAL CONCEPT #5: ViewChild Decorator
   * ========================================================================
   * @ViewChild() gives us a reference to an element in the template.
   * 
   * #messagesEnd in the template becomes this.messagesEnd in the component.
   * The '!' tells TypeScript "trust me, this will be defined"
   * 
   * Used here to scroll to the bottom when new messages arrive.
   */
  @ViewChild('messagesEnd') messagesEnd!: ElementRef;
  
  /**
   * ========================================================================
   * TECHNICAL CONCEPT #6: Output Decorator & EventEmitter
   * ========================================================================
   * @Output() allows child components to emit events to parent components.
   * 
   * EventEmitter<T> is like a custom event that can carry data.
   * Parent components can listen: <app-chat (messageSent)="handleMessage($event)">
   * 
   * This enables component communication: child -> parent
   */
  @Output() messageSent = new EventEmitter<ChatMessage>();

  // Array of all messages in the conversation
  messages: ChatMessage[] = [];
  
  // Current text in the input field (bound with [(ngModel)])
  inputMessage = '';
  
  // Loading state - true when waiting for agent response
  isLoading = false;
  
  // Unique session ID for this conversation
  sessionId = this.generateUUID();
  
  // Flag to control auto-scrolling
  private shouldScroll = false;
  
  /**
   * ========================================================================
   * TECHNICAL CONCEPT #7: RxJS Subscriptions
   * ========================================================================
   * Subscription represents an ongoing Observable subscription.
   * 
   * Why store subscriptions?
   * - So we can unsubscribe later in ngOnDestroy()
   * - Prevents memory leaks
   * - Good practice: Always clean up subscriptions!
   * 
   * We use Subscription[] to store multiple subscriptions.
   */
  private subscriptions: Subscription[] = [];
  
  // Error message to display to user (if any)
  errorMessage: string | null = null;

  /**
   * ========================================================================
   * TECHNICAL CONCEPT #8: Constructor Dependency Injection
   * ========================================================================
   * Angular's DI system automatically provides the ChatService instance.
   * 
   * The 'private' keyword:
   * 1. Declares a class property
   * 2. Assigns the injected value to it
   * 3. Makes it accessible as this.chatService
   * 
   * This is TypeScript shorthand. Without it, you'd need:
   * private chatService: ChatService;
   * constructor(chatService: ChatService) {
   *   this.chatService = chatService;
   * }
   */
  constructor(
    private chatService: ChatService,
    private cdr: ChangeDetectorRef
  ) {}

  /**
   * ========================================================================
   * TECHNICAL CONCEPT #9: UUID Generation
   * ========================================================================
   * Generates a RFC4122 version 4 compliant UUID.
   * 
   * How it works:
   * 1. Template: 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'
   * 2. Replace each 'x' and 'y' with random hex digits
   * 3. '4' indicates version 4 (random)
   * 4. 'y' becomes 8, 9, a, or b (variant bits)
   * 
   * Used for:
   * - Session tracking (groups messages in a conversation)
   * - Message IDs (unique identifier for each message)
   */
  private generateUUID(): string {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
      const r = Math.random() * 16 | 0;  // Random number 0-15
      const v = c === 'x' ? r : (r & 0x3 | 0x8);  // Bitwise operations for variant
      return v.toString(16);  // Convert to hexadecimal
    });
  }

  /**
   * ========================================================================
   * TECHNICAL CONCEPT #10: Angular Lifecycle Hooks
   * ========================================================================
   * ngAfterViewChecked() is called after Angular checks the component's view.
   * 
   * Lifecycle order:
   * 1. ngOnInit() - Component initialized
   * 2. ngAfterViewInit() - View initialized
   * 3. ngAfterViewChecked() - View checked (runs MANY times)
   * 4. ngOnDestroy() - Component destroyed
   * 
   * We use a flag (shouldScroll) to only scroll when needed,
   * not on every change detection cycle.
   */
  ngAfterViewChecked(): void {
    if (this.shouldScroll) {
      this.scrollToBottom();
      this.shouldScroll = false;
    }
  }
  
  /**
   * ========================================================================
   * TECHNICAL CONCEPT #11: Cleanup with ngOnDestroy
   * ========================================================================
   * Called when the component is destroyed (user navigates away, etc.)
   * 
   * CRITICAL: Always unsubscribe from Observables here!
   * 
   * Why?
   * - Subscriptions keep running even after component is destroyed
   * - This causes memory leaks (app uses more and more memory)
   * - Eventually, the app becomes slow or crashes
   * 
   * Best practice: Store all subscriptions and unsubscribe in ngOnDestroy
   */
  ngOnDestroy(): void {
    // Unsubscribe from all active subscriptions
    this.subscriptions.forEach(sub => sub.unsubscribe());
    console.log('Chat component destroyed, subscriptions cleaned up');
  }

  /**
   * ========================================================================
   * TECHNICAL CONCEPT #12: Sending Messages with Real API Integration
   * ========================================================================
   * This method:
   * 1. Validates input
   * 2. Creates user message and adds to UI
   * 3. Calls backend API via ChatService
   * 4. Handles response/errors
   * 5. Updates UI reactively
   */
  sendMessage(): void {
    const messageText = this.inputMessage.trim();
    
    console.log('sendMessage called with:', messageText);
    console.log('isLoading:', this.isLoading);
    console.log('sessionId:', this.sessionId);
    
    // Guard clause: Don't send empty messages or when already loading
    if (!messageText || this.isLoading) {
      console.log('Message blocked - empty or loading');
      return;
    }

    // Clear any previous error messages
    this.errorMessage = null;

    /**
     * ======================================================================
     * Step 1: Create and display user message immediately
     * ======================================================================
     * This provides instant feedback to the user.
     * We don't wait for the API - optimistic UI update!
     */
    const userMessage: ChatMessage = {
      id: this.generateUUID(),
      role: 'user',
      content: messageText,
      timestamp: new Date()
    };
    
    this.messages.push(userMessage);
    this.messageSent.emit(userMessage);  // Notify parent component
    this.inputMessage = '';  // Clear input field
    this.shouldScroll = true;  // Trigger auto-scroll
    
    // Show typing indicator (will be managed by service)
    this.isLoading = true;
    console.log('Set isLoading to true before API call');

    /**
     * ======================================================================
     * TECHNICAL CONCEPT #13: Observable Subscription
     * ======================================================================
     * .subscribe() is how we "activate" an Observable.
     * 
     * Observables are LAZY - they don't do anything until subscribed.
     * Think of it like a recipe (Observable) vs actually cooking (subscribe).
     * 
     * subscribe() takes an object with callbacks:
     * - next: Called when data arrives (success)
     * - error: Called when an error occurs
     * - complete: Called when Observable finishes (not used for HTTP)
     */
    const subscription = this.chatService.sendMessage(messageText, this.sessionId)
      .subscribe({
        /**
         * ================================================================
         * Success Handler: Called when API returns a response
         * ================================================================
         */
        next: (response) => {
          console.log('Received response from agent:', response);
          
          // Create assistant message from API response
          const assistantMessage: ChatMessage = {
            id: this.generateUUID(),
            role: 'assistant',
            content: response.message,
            timestamp: new Date()
          };
          
          // Add to messages array (Angular detects change and updates UI)
          this.messages.push(assistantMessage);
          console.log('Messages array after push:', this.messages);
          console.log('Total messages:', this.messages.length);
          console.log('Setting isLoading to false');
          this.isLoading = false;  // Hide typing indicator
          console.log('isLoading is now:', this.isLoading);
          this.shouldScroll = true;  // Scroll to new message
          
          // Force Angular to detect changes
          this.cdr.detectChanges();
          console.log('Change detection triggered');
        },
        
        /**
         * ================================================================
         * Error Handler: Called when API request fails
         * ================================================================
         * Errors can happen due to:
         * - Network issues (no internet)
         * - Server errors (backend crash)
         * - Timeout (request took too long)
         * - Invalid input (400 Bad Request)
         */
        error: (error) => {
          console.error('Chat error:', error);
          
          // Store error message to display in UI
          this.errorMessage = error.message || 'Failed to send message. Please try again.';
          
          // Create error message in chat
          const errorChatMessage: ChatMessage = {
            id: this.generateUUID(),
            role: 'assistant',
            content: `❌ ${this.errorMessage}`,
            timestamp: new Date()
          };
          
          this.messages.push(errorChatMessage);
          this.isLoading = false;
          this.shouldScroll = true;
          
          /**
           * ============================================================
           * TECHNICAL CONCEPT #14: User Feedback on Errors
           * ============================================================
           * Always provide clear, actionable error messages:
           * ❌ Bad: "Error 500"
           * ✅ Good: "Server error. Please try again in a moment."
           * 
           * Users should know:
           * 1. What went wrong
           * 2. What they can do about it
           * 3. Whether to retry or contact support
           */
        }
      });
    
    /**
     * ======================================================================
     * TECHNICAL CONCEPT #15: Memory Management
     * ======================================================================
     * Store the subscription so we can unsubscribe in ngOnDestroy().
     * This prevents memory leaks!
     */
    this.subscriptions.push(subscription);
  }

  /**
   * ========================================================================
   * TECHNICAL CONCEPT #16: Dismiss Error Messages
   * ========================================================================
   * Allow users to dismiss error messages for better UX.
   */
  dismissError(): void {
    this.errorMessage = null;
  }

  /**
   * ========================================================================
   * TECHNICAL CONCEPT #17: Safe DOM Manipulation
   * ========================================================================
   * Scroll the messages container to the bottom.
   * 
   * Why the ?. (optional chaining)?
   * - messagesEnd might be undefined during initialization
   * - nativeElement might not exist yet
   * - Prevents "Cannot read property of undefined" errors
   * 
   * scrollIntoView() is a native browser API:
   * - behavior: 'smooth' = animated scrolling
   * - behavior: 'auto' = instant jump
   */
  private scrollToBottom(): void {
    try {
      this.messagesEnd?.nativeElement?.scrollIntoView({ 
        behavior: 'smooth',
        block: 'end'  // Align to bottom of scrollable area
      });
    } catch (err) {
      // Silently ignore scroll errors (can happen during rapid updates)
      console.debug('Scroll error (safe to ignore):', err);
    }
  }

  /**
   * ========================================================================
   * TECHNICAL CONCEPT #18: Keyboard Event Handling
   * ========================================================================
   * Handle Enter key press in the input field.
   * 
   * UX Pattern:
   * - Enter = Send message
   * - Shift+Enter = New line (for multi-line messages)
   * 
   * event.preventDefault() stops the default behavior (new line on Enter)
   */
  onKeyDown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();  // Don't add newline
      this.sendMessage();      // Send the message instead
    }
    // If Shift+Enter, do nothing (allow default newline behavior)
  }

  /**
   * ========================================================================
   * TECHNICAL CONCEPT #19: Date Formatting
   * ========================================================================
   * Format timestamp for display using browser's locale.
   * 
   * toLocaleTimeString() uses the user's system locale:
   * - US: "2:30 PM"
   * - Europe: "14:30"
   * 
   * Options:
   * - hour: '2-digit' = Always show 2 digits (09 instead of 9)
   * - minute: '2-digit' = Always show 2 digits
   * 
   * Alternative: Use a library like date-fns or moment.js for more control
   */
  formatTime(date: Date): string {
    return date.toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  }

  /**
   * ========================================================================
   * TECHNICAL CONCEPT #20: State Reset
   * ========================================================================
   * Clear the conversation and start fresh.
   * 
   * Important:
   * - Generate new session ID (new conversation in backend)
   * - Clear messages array (Angular detects change and updates UI)
   * - Clear any error messages
   * 
   * This is a "soft reset" - doesn't reload the page or component.
   */
  clearChat(): void {
    this.messages = [];                    // Clear all messages
    this.sessionId = this.generateUUID(); // New session
    this.errorMessage = null;             // Clear errors
    this.isLoading = false;               // Reset loading state
    console.log('Chat cleared, new session:', this.sessionId);
  }
  
  /**
   * ========================================================================
   * Utility: Check if there are any messages
   * ========================================================================
   * Used in template to show/hide welcome message
   */
  hasMessages(): boolean {
    return this.messages.length > 0;
  }
  
  /**
   * ========================================================================
   * Utility: Get message count
   * ========================================================================
   * Useful for debugging and analytics
   */
  getMessageCount(): number {
    return this.messages.length;
  }
}
