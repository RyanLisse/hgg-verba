export type Deployment = "Weaviate" | "Docker" | "Local";

export interface Credentials {
  deployment: Deployment;
  url: string;
  key: string;
}

export interface ConnectPayload {
  credentials: Credentials;
}

export interface HealthResponse {
  message: string;
  production: string;
  gtag: string;
  deployments: Record<string, string>;
}

export interface ConversationItem { type: string; content: string }

export interface ChunksPayload { uuid: string; page: number; pageSize: number; credentials: Credentials }
export interface GetChunkPayload { uuid: string; embedder: string; credentials: Credentials }
export interface GetVectorPayload { uuid: string; showAll: boolean; credentials: Credentials }
export interface DatacountPayload { embedding_model: string; documentFilter: DocumentFilter[]; credentials: Credentials }
export interface DocumentFilter { title: string; uuid: string }
export interface GetContentPayload { uuid: string; page: number; chunkScores: ChunkScore[]; credentials: Credentials }
export interface ChunkScore { uuid: string; score: number; chunk_id: number; embedder: string }
export interface SearchQueryPayload { query: string; labels: string[]; page: number; pageSize: number; credentials: Credentials }
export interface GetDocumentPayload { uuid: string; credentials: Credentials }
export interface ResetPayload { resetMode: "ALL" | "DOCUMENTS" | "CONFIG" | "SUGGESTIONS"; credentials: Credentials }
export interface GetSuggestionsPayload { query: string; limit: number; credentials: Credentials }
export interface DeleteSuggestionPayload { uuid: string; credentials: Credentials }
export interface GetAllSuggestionsPayload { page: number; pageSize: number; credentials: Credentials }

export interface RAGComponentConfig {
  name: string;
  variables: string[];
  library: string[];
  description: string;
  config: Record<string, any>;
  type: string;
  available: boolean;
}
export interface RAGComponentClass { selected: string; components: Record<string, RAGComponentConfig> }
export interface RAGConfig { Reader: RAGComponentClass; Chunker: RAGComponentClass; Embedder: RAGComponentClass; Retriever: RAGComponentClass; Generator: RAGComponentClass }
export interface SetRAGConfigPayload { rag_config: RAGConfig; credentials: Credentials }
export interface SetUserConfigPayload { user_config: Record<string, any>; credentials: Credentials }
export interface SetThemeConfigPayload { theme: Record<string, any>; themes: Record<string, any>; credentials: Credentials }

export interface QueryPayload {
  query: string;
  RAG: Record<string, RAGComponentClass>;
  labels: string[];
  documentFilter: DocumentFilter[];
  credentials: Credentials;
}

export interface FeedbackPayload { runId: string; feedbackType: string; additionalFeedback: string; credentials: Record<string, any> }