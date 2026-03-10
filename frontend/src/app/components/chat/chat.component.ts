import {
  AfterViewChecked,
  Component,
  ElementRef,
  ViewChild,
} from '@angular/core';

import { ChatService } from '../../services/chat.service';
import { Message } from '../../models/message.model';

@Component({
  selector: 'app-chat',
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.css'],
})
export class ChatComponent implements AfterViewChecked {
  @ViewChild('messagesContainer') private messagesContainer!: ElementRef<HTMLDivElement>;

  messages: Message[] = [];
  prompt = '';
  selectedModel = 'local';
  isLoading = false;
  currentSessionId?: string;

  constructor(private chatService: ChatService) {}

  ngAfterViewChecked(): void {
    this.scrollToBottom();
  }

  sendMessage(): void {
    const trimmedPrompt = this.prompt.trim();
    if (!trimmedPrompt || this.isLoading) return;

    // Show user message immediately
    this.messages.push({ role: 'user', content: trimmedPrompt });
    this.prompt = '';
    this.isLoading = true;

    this.chatService
      .sendPrompt(trimmedPrompt, this.selectedModel, this.currentSessionId)
      .subscribe({
        next: (response) => {
          this.currentSessionId = response.chat_session_id;
          this.messages.push({ role: 'assistant', content: response.response });
          this.isLoading = false;
        },
        error: (err) => {
          console.error('Chat error:', err);
          this.messages.push({
            role: 'assistant',
            content: 'Error: could not reach the backend. Make sure it is running.',
          });
          this.isLoading = false;
        },
      });
  }

  /** Send on Enter; allow Shift+Enter for newlines. */
  onEnterKey(event: Event): void {
    const keyEvent = event as KeyboardEvent;
    if (!keyEvent.shiftKey) {
      keyEvent.preventDefault();
      this.sendMessage();
    }
  }

  private scrollToBottom(): void {
    try {
      const el = this.messagesContainer.nativeElement;
      el.scrollTop = el.scrollHeight;
    } catch (_) {}
  }
}
