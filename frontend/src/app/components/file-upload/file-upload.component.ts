import { Component, EventEmitter, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { trigger, state, style, transition, animate } from '@angular/animations';
import { ApiService, DocumentUploadResponse, UploadProgress } from '../../services/api.service';

/**
 * Represents a file in our upload queue with its current status.
 */
export interface UploadFile {
  file: File;
  progress: number;
  status: 'pending' | 'uploading' | 'complete' | 'error';
  response?: DocumentUploadResponse;
  error?: string;
}

@Component({
  selector: 'app-file-upload',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './file-upload.component.html',
  styleUrl: './file-upload.component.scss',
  animations: [
    // Animation for the progress bar - smoothly transitions width changes
    trigger('progressAnimation', [
      state('*', style({ width: '{{progress}}%' }), { params: { progress: 0 } }),
      transition('* => *', animate('300ms ease-out'))
    ]),
    // Animation for file items appearing in the list
    trigger('fadeSlideIn', [
      transition(':enter', [
        style({ opacity: 0, transform: 'translateY(-10px)' }),
        animate('200ms ease-out', style({ opacity: 1, transform: 'translateY(0)' }))
      ]),
      transition(':leave', [
        animate('200ms ease-in', style({ opacity: 0, transform: 'translateY(-10px)' }))
      ])
    ])
  ]
})
export class FileUploadComponent {
  // Event emitted when a file upload completes successfully
  @Output() uploadComplete = new EventEmitter<DocumentUploadResponse>();
  
  // Event emitted when all files in queue are processed
  @Output() allUploadsComplete = new EventEmitter<DocumentUploadResponse[]>();

  // List of files being uploaded
  uploadFiles: UploadFile[] = [];
  
  // Is the user currently dragging a file over the drop zone?
  isDragOver = false;

  // Allowed file extensions (must match backend)
  private readonly allowedExtensions = ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp'];
  
  // Max file sizes in bytes (must match backend)
  private readonly maxPdfSize = 15 * 1024 * 1024;  // 15MB
  private readonly maxImageSize = 5 * 1024 * 1024; // 5MB

  constructor(private apiService: ApiService) {}

  /**
   * Called when user drags files over the drop zone.
   * We prevent default to allow dropping and show visual feedback.
   */
  onDragOver(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragOver = true;
  }

  /**
   * Called when user drags files away from the drop zone.
   */
  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragOver = false;
  }

  /**
   * Called when user drops files onto the drop zone.
   */
  onDrop(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragOver = false;

    const files = event.dataTransfer?.files;
    if (files) {
      this.handleFiles(Array.from(files));
    }
  }

  /**
   * Called when user selects files via the file input.
   */
  onFileSelect(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files) {
      this.handleFiles(Array.from(input.files));
      input.value = ''; // Reset input so same file can be selected again
    }
  }

  /**
   * Process selected files: validate and add to upload queue.
   */
  private handleFiles(files: File[]): void {
    for (const file of files) {
      const validation = this.validateFile(file);
      
      if (validation.valid) {
        const uploadFile: UploadFile = {
          file,
          progress: 0,
          status: 'pending'
        };
        this.uploadFiles.push(uploadFile);
        this.uploadFile(uploadFile);
      } else {
        // Add file with error status to show validation error
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
   * Validate a file before uploading.
   * Checks: file extension and file size.
   */
  private validateFile(file: File): { valid: boolean; error?: string } {
    // Check extension
    const extension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!this.allowedExtensions.includes(extension)) {
      return {
        valid: false,
        error: `Invalid file type. Allowed: ${this.allowedExtensions.join(', ')}`
      };
    }

    // Check size
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
   * Upload a single file to the backend.
   * Updates the UploadFile object with progress and response.
   */
  private uploadFile(uploadFile: UploadFile): void {
    uploadFile.status = 'uploading';

    this.apiService.uploadDocument(uploadFile.file).subscribe({
      next: (progress: UploadProgress) => {
        uploadFile.progress = progress.progress;

        if (progress.status === 'complete' && progress.response) {
          uploadFile.status = progress.response.success ? 'complete' : 'error';
          uploadFile.response = progress.response;
          
          if (progress.response.success) {
            this.uploadComplete.emit(progress.response);
          } else {
            uploadFile.error = progress.response.error || progress.response.message;
          }

          this.checkAllUploadsComplete();
        }
      },
      error: (error) => {
        uploadFile.status = 'error';
        uploadFile.progress = 0;
        uploadFile.error = error.message || 'Upload failed. Please try again.';
        this.checkAllUploadsComplete();
      }
    });
  }

  /**
   * Check if all uploads are complete and emit event.
   */
  private checkAllUploadsComplete(): void {
    const allDone = this.uploadFiles.every(f => f.status === 'complete' || f.status === 'error');
    if (allDone && this.uploadFiles.length > 0) {
      const successfulResponses = this.uploadFiles
        .filter(f => f.status === 'complete' && f.response)
        .map(f => f.response!);
      this.allUploadsComplete.emit(successfulResponses);
    }
  }

  /**
   * Remove a file from the upload list.
   */
  removeFile(index: number): void {
    this.uploadFiles.splice(index, 1);
  }

  /**
   * Retry uploading a failed file.
   */
  retryUpload(uploadFile: UploadFile): void {
    uploadFile.status = 'pending';
    uploadFile.progress = 0;
    uploadFile.error = undefined;
    this.uploadFile(uploadFile);
  }

  /**
   * Format file size for display (e.g., "2.5 MB").
   */
  formatFileSize(bytes: number): string {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1024 / 1024).toFixed(1) + ' MB';
  }

  /**
   * Get icon class based on file extension.
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
