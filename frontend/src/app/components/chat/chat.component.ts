import {
  AfterViewChecked,
  Component,
  ElementRef,
  OnInit,
  ViewChild,
} from '@angular/core';

import { ChatService } from '../../services/chat.service';
import { Message } from '../../models/message.model';
import { Session, MessageResponse } from '../../models/chat-response.model';

@Component({
  selector: 'app-chat',
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.css'],
})
export class ChatComponent implements OnInit, AfterViewChecked {
  @ViewChild('messagesContainer') private messagesContainer!: ElementRef<HTMLDivElement>;

  messages: Message[] = [];
  sessions: Session[] = [];
  prompt = '';
  selectedModel = 'local';
  isLoading = false;
  currentSessionId?: string;

  constructor(private chatService: ChatService) {}

  ngOnInit(): void {
    this.loadSessions();
  }

  ngAfterViewChecked(): void {
    this.scrollToBottom();
  }

  loadSessions(): void {
    this.chatService.getSessions().subscribe({
      next: (sessions) => (this.sessions = sessions),
      error: (err) => console.error('Failed to load sessions:', err),
    });
  }

  selectSession(session: Session): void {
    this.currentSessionId = session.id;
    this.chatService.getSessionMessages(session.id).subscribe({
      next: (msgs: MessageResponse[]) => {
        this.messages = msgs.map((m) => ({
          role: m.role as 'user' | 'assistant',
          content: m.content,
        }));
      },
      error: (err) => console.error('Failed to load messages:', err),
    });
  }

  startNewChat(): void {
    this.currentSessionId = undefined;
    this.messages = [];
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
          this.loadSessions();
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

  deleteSession(session: Session, event: MouseEvent): void {
    event.stopPropagation(); // prevent triggering selectSession
    if (
      !window.confirm(
        `Delete "${session.title}"?\nThis will also remove all uploaded documents.`
      )
    ) return;

    this.chatService.deleteSession(session.id).subscribe({
      next: () => {
        if (this.currentSessionId === session.id) {
          this.currentSessionId = undefined;
          this.messages = [];
        }
        this.loadSessions();
      },
      error: (err) => console.error('Delete session failed:', err),
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
