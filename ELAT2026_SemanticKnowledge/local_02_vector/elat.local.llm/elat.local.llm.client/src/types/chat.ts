export interface ChatSession {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  messages: ChatMessage[];
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  createdAt: string;
  attachments: ChatAttachment[];
}

export interface ChatAttachment {
  id: string;
  fileName: string;
  contentType: string;
  fileSize: number;
  createdAt: string;
}

export interface CreateChatSessionRequest {
  title: string;
}

export interface SendMessageRequest {
  content: string;
  files?: File[];
}

export interface ChatStreamResponse {
  Type: 'message' | 'chunk' | 'complete' | 'error';
  Content: string;
  MessageId?: string;
  Error?: string;
}
