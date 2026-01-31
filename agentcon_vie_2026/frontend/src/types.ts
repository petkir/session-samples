export interface GroundingFile {
  chunk_id?: string;
  title?: string;
  chunk: string;
}

export interface WebSocketMessage {
  type: string;
  [key: string]: any;
}
