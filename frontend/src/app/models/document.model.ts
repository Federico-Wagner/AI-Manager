/** A document uploaded to a chat session. */
export interface Document {
  id: string;
  file_name: string;
  file_type: string;
  file_size: number;
  status: 'uploaded' | 'processing' | 'processed' | 'failed' | string;
  created_at: string;
}

/** Response from POST /sessions/{id}/documents */
export interface DocumentUploadResponse {
  document_id: string;
  status: string;
}
