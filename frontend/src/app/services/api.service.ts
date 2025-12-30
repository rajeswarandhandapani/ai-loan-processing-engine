/**
 * ============================================================================
 * API Service - Document Upload
 * ============================================================================
 * Angular service for communicating with the backend Document Intelligence API.
 * 
 * Key Concepts:
 * - HttpClient: Angular's HTTP request library
 * - Observable: Reactive data stream for async operations
 * - Progress Tracking: Monitor upload progress in real-time
 * - FormData: Browser API for multipart form uploads
 * 
 * This service handles:
 * - Document uploads with progress tracking
 * - Document type configuration
 * - Error handling for network issues
 */

import { Injectable } from '@angular/core';
import { HttpClient, HttpEvent, HttpEventType, HttpRequest } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { environment } from '../../environments/environment';


/**
 * ============================================================================
 * Upload Progress Interface
 * ============================================================================
 * Tracks the state of a file upload operation.
 * Emitted multiple times during upload to show progress.
 */
export interface UploadProgress {
  status: 'progress' | 'complete' | 'error';  // Current upload state
  progress: number;                            // 0-100 percentage
  response?: DocumentUploadResponse;           // Final response (when complete)
  error?: string;                              // Error message (if failed)
}


/**
 * ============================================================================
 * Document Analysis Interface
 * ============================================================================
 * Structure of document analysis results from Azure Document Intelligence.
 */
export interface DocumentAnalysis {
  page_count?: number;                    // Number of pages in document
  content?: string;                       // Full text content (OCR result)
  tables?: any[];                         // Extracted tables
  key_value_pairs?: Record<string, string>;  // Key-value pairs found
  entities?: any[];                       // Named entities extracted
}


/**
 * ============================================================================
 * Document Upload Response Interface
 * ============================================================================
 * Response structure from the backend /documents/upload endpoint.
 */
export interface DocumentUploadResponse {
  success: boolean;                       // Whether upload/analysis succeeded
  message: string;                        // Human-readable status message
  filename: string;                       // Original filename
  document_type: string;                  // Document type used for analysis
  analysis?: DocumentAnalysis;            // Analysis results (if successful)
  error?: string;                         // Error message (if failed)
}


/**
 * ============================================================================
 * API Service Class
 * ============================================================================
 * @Injectable({ providedIn: 'root' }) makes this a singleton service:
 * - One instance shared across the entire application
 * - Automatically available without explicit provider registration
 */
@Injectable({
  providedIn: 'root'
})
export class ApiService {
  /**
   * Backend API base URL from environment configuration.
   * Follows Open/Closed: Configuration can change without code changes.
   */
  private readonly baseUrl = environment.apiBaseUrl;

  /**
   * Constructor Dependency Injection.
   * Angular automatically provides HttpClient instance.
   */
  constructor(private http: HttpClient) {}

  /**
   * Upload a document to the backend with progress tracking.
   * 
   * How it works:
   * 1. We create a FormData object (like a virtual form with a file input)
   * 2. We use HttpRequest with reportProgress: true to get upload progress events
   * 3. We transform the events into a simple UploadProgress object
   * 
   * @param file - The file to upload
   * @param documentType - Type of document (e.g., 'prebuilt-layout', 'prebuilt-invoice')
   * @param sessionId - Optional session ID to link document to chat session
   * @returns Observable that emits progress updates and final response
   */
  uploadDocument(file: File, documentType: string = 'prebuilt-layout', sessionId?: string): Observable<UploadProgress> {
    const formData = new FormData();
    formData.append('file', file, file.name);

    // Build URL with query parameters
    let url = `${this.baseUrl}/documents/upload?document_type=${documentType}`;
    if (sessionId) {
      url += `&session_id=${sessionId}`;
    }

    const request = new HttpRequest(
      'POST',
      url,
      formData,
      {
        reportProgress: true
      }
    );

    return this.http.request(request).pipe(
      map((event: HttpEvent<any>) => this.getUploadProgress(event))
    );
  }

  /**
   * Transform HTTP events into user-friendly progress updates.
   * 
   * HttpEventType.UploadProgress - Fired during upload, contains loaded/total bytes
   * HttpEventType.Response - Fired when upload completes, contains server response
   */
  private getUploadProgress(event: HttpEvent<any>): UploadProgress {
    switch (event.type) {
      case HttpEventType.UploadProgress:
        const progress = event.total 
          ? Math.round((100 * event.loaded) / event.total) 
          : 0;
        return { status: 'progress', progress };

      case HttpEventType.Response:
        return {
          status: 'complete',
          progress: 100,
          response: event.body as DocumentUploadResponse
        };

      default:
        return { status: 'progress', progress: 0 };
    }
  }

  /**
   * Get available document types from the backend.
   */
  getDocumentTypes(): Observable<{ document_types: Array<{ value: string; name: string; description: string }> }> {
    return this.http.get<{ document_types: Array<{ value: string; name: string; description: string }> }>(
      `${this.baseUrl}/documents/types`
    );
  }
}
