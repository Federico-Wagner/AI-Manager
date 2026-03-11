import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';
import { ChatResponse, MessageResponse, Session } from '../models/chat-response.model';

@Injectable({ providedIn: 'root' })
export class ChatService {
  private readonly apiUrl = environment.apiBaseUrl;

  constructor(private http: HttpClient) {}

  /**
   * Send a prompt to the backend and receive an AI response.
   * Optionally pass an existing session ID to continue a conversation.
   */
  sendPrompt(
    prompt: string,
    model: string,
    chatSessionId?: string
  ): Observable<ChatResponse> {
    return this.http.post<ChatResponse>(`${this.apiUrl}/chat/`, {
      prompt,
      model,
      chat_session_id: chatSessionId ?? null,
    });
  }

  /** Retrieve all chat sessions. */
  getSessions(): Observable<Session[]> {
    return this.http.get<Session[]>(`${this.apiUrl}/chat/sessions`);
  }

  /** Retrieve all messages for a specific session. */
  getSessionMessages(sessionId: string): Observable<MessageResponse[]> {
    return this.http.get<MessageResponse[]>(
      `${this.apiUrl}/chat/sessions/${sessionId}`
    );
  }

  /** Create a new named chat session. */
  createSession(title: string): Observable<Session> {
    return this.http.post<Session>(`${this.apiUrl}/chat/sessions`, { title });
  }

  /** Delete a chat session and all associated data. */
  deleteSession(sessionId: string): Observable<{ message: string }> {
    return this.http.delete<{ message: string }>(
      `${this.apiUrl}/chat/sessions/${sessionId}`
    );
  }
}
