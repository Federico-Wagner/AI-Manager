import {
  Component,
  Input,
  OnChanges,
  SimpleChanges,
} from '@angular/core';

import { DocumentService } from '../../services/document.service';
import { Document } from '../../models/document.model';

@Component({
  selector: 'app-documents-panel',
  templateUrl: './documents-panel.component.html',
  styleUrls: ['./documents-panel.component.css'],
})
export class DocumentsPanelComponent implements OnChanges {
  @Input() sessionId?: string;

  documents: Document[] = [];
  isDragging = false;
  isUploading = false;
  errorMessage = '';

  constructor(private documentService: DocumentService) {}

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['sessionId']) {
      if (this.sessionId) {
        this.loadDocuments();
      } else {
        this.documents = [];
        this.errorMessage = '';
      }
    }
  }

  loadDocuments(): void {
    if (!this.sessionId) return;
    this.documentService.getDocuments(this.sessionId).subscribe({
      next: (docs) => (this.documents = docs),
      error: (err) => {
        console.error('Failed to load documents:', err);
        this.errorMessage = 'Could not load documents.';
      },
    });
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (file) {
      this.upload(file);
      input.value = '';
    }
  }

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    this.isDragging = true;
  }

  onDragLeave(): void {
    this.isDragging = false;
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    this.isDragging = false;
    const file = event.dataTransfer?.files[0];
    if (file) {
      this.upload(file);
    }
  }

  upload(file: File): void {
    if (!this.sessionId) {
      this.errorMessage = 'Select a chat session before uploading.';
      return;
    }
    this.errorMessage = '';
    this.isUploading = true;

    this.documentService.uploadDocument(this.sessionId, file).subscribe({
      next: () => {
        this.isUploading = false;
        this.loadDocuments();
      },
      error: (err) => {
        console.error('Upload failed:', err);
        this.isUploading = false;
        this.errorMessage =
          err?.error?.detail ?? 'Upload failed. Check the file type.';
      },
    });
  }

  confirmDelete(doc: Document): void {
    if (!window.confirm(`Delete "${doc.file_name}"?`)) return;

    this.documentService.deleteDocument(doc.id).subscribe({
      next: () => {
        this.documents = this.documents.filter((d) => d.id !== doc.id);
      },
      error: (err) => {
        console.error('Delete failed:', err);
        this.errorMessage = 'Could not delete document.';
      },
    });
  }

  statusLabel(status: string): string {
    const labels: Record<string, string> = {
      uploaded: 'Uploaded',
      processing: 'Processing…',
      processed: 'Ready',
      failed: 'Failed',
    };
    return labels[status] ?? status;
  }
}
