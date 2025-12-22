import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ChatComponent } from '../../components/chat/chat';
import { FileUploadComponent } from '../../components/file-upload/file-upload.component';

interface UploadedDocument {
  filename: string;
  document_type: string;
  analysis?: {
    document_type?: string;
    fields?: Record<string, any>;
    pages?: any[];
    content?: string;
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
        document_type: result.document_type,
        analysis: result.analysis
      }]);
    }
  }

  getExtractedFields(doc: UploadedDocument): Array<{key: string, value: any}> {
    if (!doc.analysis?.fields) return [];
    
    return Object.entries(doc.analysis.fields)
      .filter(([_, field]: [string, any]) => field.value !== null && field.value !== undefined)
      .map(([key, field]: [string, any]) => ({
        key: this.formatFieldName(key),
        value: field.value
      }));
  }

  private formatFieldName(name: string): string {
    return name.replace(/([A-Z])/g, ' $1').trim();
  }

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

  onChatMessageSent(message: any): void {
    console.log('Chat message sent:', message);
  }
}
