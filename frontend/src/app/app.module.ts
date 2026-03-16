import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';

import { AppComponent } from './app.component';
import { ChatComponent } from './components/chat/chat.component';
import { DocumentsPanelComponent } from './components/documents-panel/documents-panel.component';
import { MarkdownPipe } from './pipes/markdown.pipe';

@NgModule({
  declarations: [AppComponent, ChatComponent, DocumentsPanelComponent, MarkdownPipe],
  imports: [BrowserModule, FormsModule, HttpClientModule],
  bootstrap: [AppComponent],
})
export class AppModule {}
