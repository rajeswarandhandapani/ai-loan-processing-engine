/**
 * ============================================================================
 * File Upload Component
 * ============================================================================
 * Drag-and-drop file upload with progress tracking and validation.
 * 
 * Key Concepts:
 * - Drag & Drop API: Native browser API for file dragging
 * - File Validation: Check type and size before upload
 * - Progress Tracking: Real-time upload progress via HttpEvent
 * - Queue Management: Handle multiple files simultaneously
 * 
 * Features:
 * - Drag and drop or click to select files
 * - Visual progress indicators
 * - File type and size validation
 * - Auto-detect document type from filename
 * - Retry failed uploads
 * - Session linking for chat integration
 */

import { Component, EventEmitter, Output, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService, DocumentUploadResponse, UploadProgress } from '../../services/api.service';


/**
 * ============================================================================
 * Upload File Interface
 * ============================================================================
 * Tracks the state of each file in the upload queue.
 * Updated throughout the upload lifecycle.
 */
export interface UploadFile {
  file: File;                    // The actual File object from browser
  progress: number;              // Upload progress 0-100
  status: 'pending' | 'uploading' | 'complete' | 'error';  // Current state
  response?: DocumentUploadResponse;  // Server response (when complete)
  error?: string;                     // Error message (if failed)
}

/**
 * ============================================================================
 * Component Decorator
 * ============================================================================
 * Note: Animations are now handled via native CSS in the SCSS file.
 * As of Angular v20.2, @angular/animations is deprecated.
 * Use CSS transitions/animations with animate.enter and animate.leave instead.
 */
@Component({
  selector: 'app-file-upload',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './file-upload.component.html',
  styleUrl: './file-upload.component.scss'
})
export class FileUploadComponent {
  /**
   * ========================================================================
   * Input Properties
   * ========================================================================
   * @Input() allows parent components to pass data to this component.
   * Usage: <app-file-upload [sessionId]="currentSessionId">
   */
  @Input() sessionId: string = '';  // Links uploads to chat session

  /**
   * ========================================================================
   * Output Events
   * ========================================================================
   * @Output() allows this component to emit events to parent components.
   * Usage: <app-file-upload (uploadComplete)="handleUpload($event)">
   */
  @Output() uploadComplete = new EventEmitter<DocumentUploadResponse>();
  @Output() allUploadsComplete = new EventEmitter<DocumentUploadResponse[]>();

  /**
   * ========================================================================
   * Component State
   * ========================================================================
   */
  uploadFiles: UploadFile[] = [];  // Queue of files being processed
  isDragOver = false;              // Visual feedback for drag state

  /**
   * ========================================================================
   * Validation Configuration
   * ========================================================================
   * These limits must match the backend to avoid server-side rejections.
   * Keep in sync with: backend/app/routers/document_intelligence_router.py
   */
  private readonly allowedExtensions = ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp'];
  private readonly maxPdfSize = 15 * 1024 * 1024;   // 15MB for PDFs
  private readonly maxImageSize = 5 * 1024 * 1024;  // 5MB for images

  /**
   * Constructor with Dependency Injection.
   * ApiService is injected to handle HTTP uploads.
   */
  constructor(private apiService: ApiService) {}

  /**
   * ========================================================================
   * Drag & Drop Event Handlers
   * ========================================================================
   * Browser Drag & Drop API events:
   * - dragover: Fired continuously while dragging over element
   * - dragleave: Fired when drag leaves element
   * - drop: Fired when file is dropped
   * 
   * preventDefault() is required for drop to work!
   */

  /**
   * Handle dragover - show visual feedback and allow drop.
   */
  onDragOver(event: DragEvent): void {
    event.preventDefault();     // Required for drop to work
    event.stopPropagation();    // Don't bubble to parent elements
    this.isDragOver = true;     // Show visual feedback
  }

  /**
   * Handle dragleave - remove visual feedback.
   */
  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragOver = false;
  }

  /**
   * Handle drop - process the dropped files.
   */
  onDrop(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragOver = false;

    // dataTransfer contains the dropped files
    const files = event.dataTransfer?.files;
    if (files) {
      this.handleFiles(Array.from(files));
    }
  }

  /**
   * Handle file selection via traditional input[type="file"].
   */
  onFileSelect(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files) {
      this.handleFiles(Array.from(input.files));
      input.value = '';  // Reset so same file can be selected again
    }
  }

  /**
   * ========================================================================
   * File Processing
   * ========================================================================
   * Validate files and add them to the upload queue.
   */

  /**
   * Process an array of files: validate and start uploads.
   */
  private handleFiles(files: File[]): void {
    for (const file of files) {
      const validation = this.validateFile(file);
      
      if (validation.valid) {
        // Valid file - add to queue and start upload
        const uploadFile: UploadFile = {
          file,
          progress: 0,
          status: 'pending'
        };
        this.uploadFiles.push(uploadFile);
        this.uploadFile(uploadFile);
      } else {
        // Invalid file - add with error status for user feedback
        this.uploadFiles.push({
          file,
          progress: 0,
          status: 'error',
          error: validation.error
        });
      }
    }
  }

  /**
   * ========================================================================
   * File Validation
   * ========================================================================
   * Validate file type and size before uploading.
   * Returns validation result with optional error message.
   */
  private validateFile(file: File): { valid: boolean; error?: string } {
    // === Extension Check ===
    const extension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!this.allowedExtensions.includes(extension)) {
      return {
        valid: false,
        error: `Invalid file type. Allowed: ${this.allowedExtensions.join(', ')}`
      };
    }

    // === Size Check ===
    // PDFs get larger limit than images
    const maxSize = extension === '.pdf' ? this.maxPdfSize : this.maxImageSize;
    if (file.size > maxSize) {
      const maxSizeMB = maxSize / 1024 / 1024;
      return {
        valid: false,
        error: `File too large. Maximum size: ${maxSizeMB}MB`
      };
    }

    return { valid: true };
  }

  /**
   * ========================================================================
   * Document Type Detection
   * ========================================================================
   * Automatically detect document type based on filename patterns.
   * This helps users by auto-selecting the right analysis model.
   * 
   * Pattern matching is case-insensitive:
   * - "bank_statement_2024.pdf" -> bank_statement
   * - "Invoice-001.pdf" -> invoice
   * - "receipt.jpg" -> receipt
   * - "W2_2023.pdf" -> tax_w2
   * - "document.pdf" -> prebuilt-layout (default)
   */
  private getDocumentType(filename: string): string {
    const lower = filename.toLowerCase();
    
    // Bank statements
    if (lower.includes('bank') || lower.includes('statement')) {
      return 'bank_statement';
    }
    
    // Invoices
    if (lower.includes('invoice')) {
      return 'invoice';
    }
    
    // Receipts
    if (lower.includes('receipt')) {
      return 'receipt';
    }
    
    // W-2 tax forms
    if (lower.includes('w2') || lower.includes('w-2') || lower.includes('tax')) {
      return 'tax_w2';
    }
    
    // Default: general layout analysis
    return 'prebuilt-layout';
  }

  /**
   * ========================================================================
   * Upload Execution
   * ========================================================================
   * Performs the actual HTTP upload with progress tracking.
   */

  /**
   * Upload a single file to the backend.
   * 
   * Observable subscription provides:
   * - next: Called multiple times with progress updates
   * - error: Called once if upload fails
   * - complete: Called when Observable finishes (we don't use this)
   */
  private uploadFile(uploadFile: UploadFile): void {
    uploadFile.status = 'uploading';
    
    // Auto-detect document type from filename
    const documentType = this.getDocumentType(uploadFile.file.name);

    this.apiService.uploadDocument(uploadFile.file, documentType, this.sessionId).subscribe({
      // === Progress Updates ===
      next: (progress: UploadProgress) => {
        uploadFile.progress = progress.progress;

        // Check if upload completed
        if (progress.status === 'complete' && progress.response) {
          uploadFile.status = progress.response.success ? 'complete' : 'error';
          uploadFile.response = progress.response;
          
          // Emit success event to parent
          if (progress.response.success) {
            this.uploadComplete.emit(progress.response);
          } else {
            uploadFile.error = progress.response.error || progress.response.message;
          }

          this.checkAllUploadsComplete();
        }
      },
      // === Error Handler ===
      error: (error) => {
        uploadFile.status = 'error';
        uploadFile.progress = 0;
        uploadFile.error = error.message || 'Upload failed. Please try again.';
        this.checkAllUploadsComplete();
      }
    });
  }

  /**
   * ========================================================================
   * Queue Management
   * ========================================================================
   * Methods for managing the upload queue.
   */

  /**
   * Check if all uploads are complete and emit batch event.
   */
  private checkAllUploadsComplete(): void {
    const allDone = this.uploadFiles.every(f => f.status === 'complete' || f.status === 'error');
    if (allDone && this.uploadFiles.length > 0) {
      // Collect all successful responses
      const successfulResponses = this.uploadFiles
        .filter(f => f.status === 'complete' && f.response)
        .map(f => f.response!);
      this.allUploadsComplete.emit(successfulResponses);
    }
  }

  /**
   * Remove a file from the upload list (user dismissed it).
   */
  removeFile(index: number): void {
    this.uploadFiles.splice(index, 1);
  }

  /**
   * Retry a failed upload.
   */
  retryUpload(uploadFile: UploadFile): void {
    uploadFile.status = 'pending';
    uploadFile.progress = 0;
    uploadFile.error = undefined;
    this.uploadFile(uploadFile);
  }

  /**
   * ========================================================================
   * Utility Methods - Display Formatting
   * ========================================================================
   */

  /**
   * Format file size for human-readable display.
   * Examples: "512 B", "2.5 KB", "1.2 MB"
   */
  formatFileSize(bytes: number): string {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1024 / 1024).toFixed(1) + ' MB';
  }

  /**
   * Get Bootstrap icon class based on file extension.
   * Used in template for file type icons.
   */
  getFileIcon(filename: string): string {
    const ext = filename.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'pdf': return 'bi-file-earmark-pdf';
      case 'png':
      case 'jpg':
      case 'jpeg':
      case 'bmp':
      case 'tiff': return 'bi-file-earmark-image';
      default: return 'bi-file-earmark';
    }
  }
}
