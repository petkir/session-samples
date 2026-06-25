export interface KnowledgeSearchResult {
  documentId: string;
  content: string;
  relevanceScore: number;
  fileName?: string;
  category?: string;
  addedAt?: string;
}

export interface AddDocumentRequest {
  content: string;
  fileName?: string;
  category?: string;
}

export interface AddDocumentResponse {
  documentId: string;
  message: string;
}

export interface SearchRequest {
  query: string;
  maxResults: number;
}

export interface SearchResponse {
  results: KnowledgeSearchResult[];
  totalResults: number;
  query: string;
}

export interface UploadFileRequest {
  file: File;
  category?: string;
}

export interface KnowledgeDocument {
  id: string;
  fileName?: string;
  category?: string;
  content: string;
  addedAt?: string;
  contentLength?: number;
}
