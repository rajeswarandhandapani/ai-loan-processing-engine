/**
 * ============================================================================
 * Home Component - Main Application Page
 * ============================================================================
 * The main page that combines chat and document upload functionality.
 * 
 * Key Concepts:
 * - Container Component: Orchestrates child components
 * - Signals: Angular's new reactive primitive (Angular 16+)
 * - Component Communication: Parent-child data flow via @Input/@Output
 * 
 * Layout:
 * +------------------------------------------+
 * |              Header                      |
 * +------------------+-----------------------+
 * |                  |                       |
 * |   File Upload    |     Chat Interface    |
 * |                  |                       |
 * |   Uploaded Docs  |                       |
 * |     Summary      |                       |
 * +------------------+-----------------------+
 */

import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ChatComponent } from '../../components/chat/chat';
import { FileUploadComponent } from '../../components/file-upload/file-upload.component';


/**
 * ============================================================================
 * Uploaded Document Interface
 * ============================================================================
 * Represents a document that has been uploaded and analyzed.
 * Used to display document summaries in the sidebar.
 */
interface UploadedDocument {
  filename: string;              // Original filename
  document_type: string;         // Type used for analysis
  analysis?: {                   // Analysis results from backend
    document_type?: string;
    fields?: Record<string, any>;  // Extracted key-value pairs
    pages?: any[];                 // Page information
    content?: string;              // Full text content
  };
}


/**
 * ============================================================================
 * Home Component Decorator
 * ============================================================================
 */
@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, ChatComponent, FileUploadComponent],
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss']
})
export class HomeComponent {
  /**
   * ========================================================================
   * Angular Signals
   * ========================================================================
   * signal<T>() creates a reactive value that:
   * - Automatically triggers change detection when updated
   * - More efficient than zone.js change detection
   * - Works with Angular's new reactivity system
   * 
   * Usage:
   * - Read: this.uploadedDocuments()
   * - Write: this.uploadedDocuments.set([...])
   * - Update: this.uploadedDocuments.update(docs => [...docs, newDoc])
   */
  uploadedDocuments = signal<UploadedDocument[]>([]);
  
  /**
   * Current chat session ID - shared with file upload component
   * to link uploaded documents to the current conversation.
   */
  currentSessionId: string = '';

  /**
   * ========================================================================
   * Event Handlers - Component Communication
   * ========================================================================
   * These methods handle events emitted by child components.
   * This is how child-to-parent communication works in Angular:
   * 
   * Child: @Output() sessionIdChanged = new EventEmitter<string>();
   * Parent: <app-chat (sessionIdChanged)="onSessionIdChanged($event)">
   */

  /**
   * Called when the chat component generates a new session ID.
   * Updates local state so file uploads can be linked to the session.
   */
  onSessionIdChanged(sessionId: string): void {
    this.currentSessionId = sessionId;
    console.log('Session ID updated:', sessionId);
  }

  /**
   * Called when a document upload completes successfully.
   * Adds the document to our local list for display in the sidebar.
   */
  onUploadComplete(result: any): void {
    if (result.success) {
      this.uploadedDocuments.update(docs => [...docs, {
        filename: result.filename,
        document_type: result.document_type,
        analysis: result.analysis
      }]);
    }
  }

  /**
   * ========================================================================
   * Utility Methods - Data Transformation
   * ========================================================================
   * Helper methods for transforming and formatting data for display.
   */

  /**
   * Extract key-value fields from a document's analysis results.
   * Filters out null/undefined values and formats field names.
   */
  getExtractedFields(doc: UploadedDocument): Array<{key: string, value: any}> {
    if (!doc.analysis?.fields) return [];
    
    return Object.entries(doc.analysis.fields)
      .filter(([_, field]: [string, any]) => field.value !== null && field.value !== undefined)
      .map(([key, field]: [string, any]) => ({
        key: this.formatFieldName(key),
        value: field.value
      }));
  }

  /**
   * Convert camelCase or PascalCase field names to human-readable format.
   * Example: "AccountHolderName" -> "Account Holder Name"
   */
  private formatFieldName(name: string): string {
    return name.replace(/([A-Z])/g, ' $1').trim();
  }

  /**
   * Get a user-friendly label for document types.
   * Maps backend document type codes to display names.
   */
  getDocumentTypeLabel(docType: string): string {
    const labels: Record<string, string> = {
      'bank_statement': 'Bank Statement',
      'invoice': 'Invoice',
      'receipt': 'Receipt',
      'tax_w2': 'W-2 Tax Form',
      'prebuilt-layout': 'General Document'
    };
    return labels[docType] || docType;
  }

  /**
   * Handle chat message events (for logging/analytics).
   * Currently just logs - could be extended for analytics tracking.
   */
  onChatMessageSent(message: any): void {
    console.log('Chat message sent:', message);
  }
}
