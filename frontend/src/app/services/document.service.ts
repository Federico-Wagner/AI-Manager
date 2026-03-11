import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';
import { Document, DocumentUploadResponse } from '../models/document.model';

@Injectable({ providedIn: 'root' })
export class DocumentService {
  private readonly apiUrl = environment.apiBaseUrl;

  constructor(private http: HttpClient) {}

  /** Retrieve all documents for a chat session. */
  getDocuments(sessionId: string): Observable<Document[]> {
    return this.http.get<Document[]>(
      `${this.apiUrl}/sessions/${sessionId}/documents`
    );
  }

  /** Upload a file to a chat session. */
  uploadDocument(
    sessionId: string,
    file: File
  ): Observable<DocumentUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<DocumentUploadResponse>(
      `${this.apiUrl}/sessions/${sessionId}/documents`,
      formData
    );
  }

  /** Delete a document by ID. */
  deleteDocument(documentId: string): Observable<{ message: string }> {
    return this.http.delete<{ message: string }>(
      `${this.apiUrl}/sessions/documents/${documentId}`
    );
  }
}
