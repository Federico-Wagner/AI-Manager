/** A single message in a conversation thread. */
export interface Message {
  role: 'user' | 'assistant';
  content: string;
}
