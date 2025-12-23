import { Injectable } from '@angular/core';
import { HttpClient, HttpEvent, HttpEventType, HttpRequest } from '@angular/common/http';
import { Observable, map } from 'rxjs';

export interface UploadProgress {
  status: 'progress' | 'complete' | 'error';
  progress: number;
  response?: DocumentUploadResponse;
  error?: string;
}

export interface DocumentAnalysis {
  page_count?: number;
  content?: string;
  tables?: any[];
  key_value_pairs?: Record<string, string>;
  entities?: any[];
}

export interface DocumentUploadResponse {
  success: boolean;
  message: string;
  filename: string;
  document_type: string;
  analysis?: DocumentAnalysis;
  error?: string;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private readonly baseUrl = 'http://localhost:8000/api/v1';

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
