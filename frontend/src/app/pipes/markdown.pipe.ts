import { Pipe, PipeTransform } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';

@Pipe({ name: 'markdown' })
export class MarkdownPipe implements PipeTransform {
  constructor(private sanitizer: DomSanitizer) {}

  transform(text: string): SafeHtml {
    if (!text) return '';

    // 1. Escape raw HTML to prevent XSS
    let html = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    // 2. Apply markdown patterns
    // Bold: **text**
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    // Italic: *text* (not already matched by bold)
    html = html.replace(/\*([^*\n]+?)\*/g, '<em>$1</em>');
    // Inline code: `code`
    html = html.replace(/`([^`\n]+)`/g, '<code>$1</code>');

    return this.sanitizer.bypassSecurityTrustHtml(html);
  }
}
