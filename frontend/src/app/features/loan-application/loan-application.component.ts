import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FileUploadComponent } from '../../components/file-upload/file-upload.component';
import { ChatComponent, ChatMessage } from '../../components/chat/chat';
import { DocumentUploadResponse } from '../../services/api.service';

@Component({
  selector: 'app-loan-application',
  standalone: true,
  imports: [CommonModule, FileUploadComponent, ChatComponent],
  templateUrl: './loan-application.component.html',
  styleUrl: './loan-application.component.scss'
})
export class LoanApplicationComponent {
  // Store uploaded document responses for display in Step 2
  uploadedDocuments: DocumentUploadResponse[] = [];

  /**
   * Called when a single file upload completes.
   * We store the response to display extracted data in Step 2.
   */
  onUploadComplete(response: DocumentUploadResponse): void {
    console.log('Upload complete:', response);
    this.uploadedDocuments.push(response);
  }

  /**
   * Called when all files in the queue are processed.
   */
  onAllUploadsComplete(responses: DocumentUploadResponse[]): void {
    console.log('All uploads complete:', responses);
  }

  /**
   * Called when a chat message is sent.
   */
  onChatMessageSent(message: ChatMessage): void {
    console.log('Chat message sent:', message);
  }
}
