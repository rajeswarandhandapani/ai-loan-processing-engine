import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ChatComponent } from '../../components/chat/chat';
import { FileUploadComponent } from '../../components/file-upload/file-upload.component';

interface UploadedDocument {
  filename: string;
  analysis?: {
    page_count?: number;
    key_value_pairs?: Record<string, any>;
  };
}

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, ChatComponent, FileUploadComponent],
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss']
})
export class HomeComponent {
  uploadedDocuments = signal<UploadedDocument[]>([]);

  onUploadComplete(result: any): void {
    if (result.success) {
      this.uploadedDocuments.update(docs => [...docs, {
        filename: result.filename,
        analysis: result.analysis
      }]);
    }
  }

  onChatMessageSent(message: any): void {
    console.log('Chat message sent:', message);
  }
}
