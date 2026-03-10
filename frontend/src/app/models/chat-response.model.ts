/** Response from POST /chat */
export interface ChatResponse {
  chat_session_id: string;
  response: string;
}

/** Response from GET /chat/sessions */
export interface Session {
  id: string;
  title: string;
  created_at: string;
}

/** Response from GET /chat/sessions/{id} */
export interface MessageResponse {
  id: string;
  chat_session_id: string;
  role: string;
  content: string;
  created_at: string;
}
