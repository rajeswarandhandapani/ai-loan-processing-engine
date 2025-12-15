import { Component, ElementRef, ViewChild, AfterViewChecked, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { trigger, transition, style, animate } from '@angular/animations';

/**
 * Represents a single chat message in the conversation.
 */
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chat.html',
  styleUrl: './chat.scss',
  animations: [
    // Animation for messages appearing
    trigger('messageAnimation', [
      transition(':enter', [
        style({ opacity: 0, transform: 'translateY(10px)' }),
        animate('200ms ease-out', style({ opacity: 1, transform: 'translateY(0)' }))
      ])
    ])
  ]
})
export class ChatComponent implements AfterViewChecked {
  // Reference to the scroll anchor element for auto-scrolling
  @ViewChild('messagesEnd') messagesEnd!: ElementRef;
  
  // Event emitted when a message is sent (for parent component awareness)
  @Output() messageSent = new EventEmitter<ChatMessage>();

  // Array of all messages in the conversation
  messages: ChatMessage[] = [];
  
  // Current text in the input field
  inputMessage = '';
  
  // Loading state - true when waiting for agent response
  isLoading = false;
  
  // Unique session ID for this conversation (will be used by API in Day 19)
  sessionId = this.generateUUID();
  
  // Flag to control auto-scrolling
  private shouldScroll = false;

  /**
   * Generate a UUID for session tracking.
   * Using a simple implementation for browser compatibility.
   */
  private generateUUID(): string {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
      const r = Math.random() * 16 | 0;
      const v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }

  /**
   * Lifecycle hook - called after every view check.
   * Used to scroll to bottom when new messages arrive.
   */
  ngAfterViewChecked(): void {
    if (this.shouldScroll) {
      this.scrollToBottom();
      this.shouldScroll = false;
    }
  }

  /**
   * Send a message from the user.
   * Creates user message, shows typing indicator, and simulates agent response.
   * (Day 19 will replace simulation with actual API call)
   */
  sendMessage(): void {
    const messageText = this.inputMessage.trim();
    if (!messageText || this.isLoading) return;

    // Create and add user message
    const userMessage: ChatMessage = {
      id: this.generateUUID(),
      role: 'user',
      content: messageText,
      timestamp: new Date()
    };
    
    this.messages.push(userMessage);
    this.messageSent.emit(userMessage);
    this.inputMessage = '';
    this.shouldScroll = true;
    
    // Show typing indicator
    this.isLoading = true;

    // Simulate agent response (will be replaced with API call in Day 19)
    this.simulateAgentResponse(messageText);
  }

  /**
   * Simulate an agent response for UI testing.
   * This will be replaced with actual API integration in Day 19.
   */
  private simulateAgentResponse(userMessage: string): void {
    // Simulate network delay (1-2 seconds)
    const delay = 1000 + Math.random() * 1000;
    
    setTimeout(() => {
      const responses = [
        `I've received your message about "${userMessage.substring(0, 30)}${userMessage.length > 30 ? '...' : ''}". Let me help you with your loan application.`,
        'Thank you for providing that information. Based on your uploaded documents, I can see the financial details. Would you like me to summarize them?',
        'I understand. As your AI loan assistant, I can help analyze your financial documents and answer questions about the loan process.',
        'That\'s a great question! Our lending policies are designed to be flexible. Let me check the relevant guidelines for you.'
      ];
      
      const agentMessage: ChatMessage = {
        id: this.generateUUID(),
        role: 'assistant',
        content: responses[Math.floor(Math.random() * responses.length)],
        timestamp: new Date()
      };
      
      this.messages.push(agentMessage);
      this.isLoading = false;
      this.shouldScroll = true;
    }, delay);
  }

  /**
   * Scroll the messages container to the bottom.
   * Uses smooth scrolling for better UX.
   */
  private scrollToBottom(): void {
    try {
      this.messagesEnd?.nativeElement?.scrollIntoView({ behavior: 'smooth' });
    } catch (err) {
      // Ignore scroll errors
    }
  }

  /**
   * Handle Enter key press in the input field.
   * Sends message on Enter, allows Shift+Enter for new lines.
   */
  onKeyDown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }

  /**
   * Format timestamp for display.
   */
  formatTime(date: Date): string {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  /**
   * Clear the conversation and start fresh.
   */
  clearChat(): void {
    this.messages = [];
    this.sessionId = this.generateUUID();
  }
}
