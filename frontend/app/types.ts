export type Credentials = {
  deployment: "Weaviate" | "Docker" | "Local";
  url: string;
  key: string;
};

export type DocumentFilter = {
  title: string;
  uuid: string;
};

export type UserConfig = {
  getting_started: boolean;
};

export type ConnectPayload = {
  connected: boolean;
  error: string;
  rag_config: RAGConfig;
  user_config: UserConfig;
  theme: Theme;
  themes: Themes;
};

export type StatusMessage = {
  message: string;
  timestamp: string;
  type: "INFO" | "WARNING" | "SUCCESS" | "ERROR";
};

export type Suggestion = {
  query: string;
  timestamp: string;
  uuid: string;
};

export type SuggestionsPayload = {
  suggestions: Suggestion[];
};

export type AllSuggestionsPayload = {
  suggestions: Suggestion[];
  total_count: number;
};

export type StatusPayload = {
  type: string;
  variables: Status;
  libraries: Status;
  schemas: SchemaStatus;
  error: string;
};

export type HealthPayload = {
  message: string;
  production: "Local" | "Demo" | "Production";
  gtag: string;
  deployments: {
    WEAVIATE_URL_VERBA: string;
    WEAVIATE_API_KEY_VERBA: string;
  };
};

export type QueryPayload = {
  error: string;
  documents: DocumentScore[];
  context: string;
};

export type DocumentScore = {
  title: string;
  uuid: string;
  score: number;
  chunks: ChunkScore[];
};

export type ChunkScore = {
  uuid: string;
  chunk_id: number;
  score: number;
  embedder: string;
};

export type Status = {
  [key: string]: boolean;
};

export type SchemaStatus = {
  [key: string]: number;
};

export type RAGConfigResponse = {
  rag_config: RAGConfig;
  error: string;
};

export type UserConfigResponse = {
  user_config: UserConfig;
  error: string;
};

export type ThemeConfigResponse = {
  themes: Themes | null;
  theme: Theme | null;
  error: string;
};

export type DatacountResponse = {
  datacount: number;
};

export type LabelsResponse = {
  labels: string[];
};

export type ImportResponse = {
  logging: ConsoleMessage[];
};

export type ConsoleMessage = {
  type: "INFO" | "WARNING" | "SUCCESS" | "ERROR";
  message: string;
};

export type RAGConfig = {
  [componentTitle: string]: RAGComponentClass;
};

export type RAGComponentClass = {
  selected: string;
  components: RAGComponent;
};

export type RAGComponent = {
  [key: string]: RAGComponentConfig;
};

export type RAGComponentConfig = {
  name: string;
  variables: string[];
  library: string[];
  description: string[];
  selected: string;
  config: RAGSetting;
  type: string;
  available: boolean | string;
};

export type ConfigSetting = {
  type: string;
  value: string | number | boolean;
  description: string;
  values?: string[];
};

export type RAGSetting = {
  [key: string]: ConfigSetting;
};

export type FileData = {
  fileID: string;
  filename: string;
  isURL: boolean;
  overwrite: boolean;
  extension: string;
  source: string;
  content: string;
  labels: string[];
  metadata: string;
  file_size: number;
  block?: boolean;
  status_report: StatusReportMap;
  status:
    | "READY"
    | "STARTING"
    | "LOADING"
    | "CHUNKING"
    | "EMBEDDING"
    | "INGESTING"
    | "NER"
    | "EXTRACTION"
    | "SUMMARIZING"
    | "WAITING"
    | "DONE"
    | "ERROR";
  rag_config: RAGConfig;
};

export type StatusReportMap = {
  [key: string]: StatusReport;
};

export type StatusReport = {
  fileID: string;
  status:
    | "READY"
    | "STARTING"
    | "LOADING"
    | "CHUNKING"
    | "EMBEDDING"
    | "INGESTING"
    | "NER"
    | "EXTRACTION"
    | "SUMMARIZING"
    | "DONE"
    | "WAITING"
    | "ERROR";
  message: string;
  took: number;
};

export type CreateNewDocument = {
  new_file_id: string;
  filename: string;
  original_file_id: string;
};

export const statusColorMap = {
  DONE: "bg-secondary-verba",
  ERROR: "bg-warning-verba",
  READY: "bg-button-verba",
  STARTING: "bg-button-verba",
  CHUNKING: "bg-button-verba",
  LOADING: "bg-button-verba",
  EMBEDDING: "bg-button-verba",
  INGESTING: "bg-button-verba",
  NER: "bg-button-verba",
  EXTRACTION: "bg-button-verba",
  SUMMARIZING: "bg-button-verba",
  WAITING: "bg-button-verba",
};

export const statusTextMap = {
  DONE: "Finished",
  ERROR: "Failed",
  READY: "Ready",
  STARTING: "Importing...",
  CHUNKING: "Chunking...",
  LOADING: "Loading...",
  EMBEDDING: "Embedding...",
  INGESTING: "Weaviating...",
  NER: "Extracting NER...",
  EXTRACTION: "Extraction REL...",
  SUMMARIZING: "Summarizing...",
  WAITING: "Uploading...",
};

export type FileMap = {
  [key: string]: FileData;
};

export type MetaData = {
  content: string;
  enable_ner: boolean;
  ner_labels: string[];
};

export type DocumentChunk = {
  text: string;
  doc_name: string;
  chunk_id: number;
  doc_uuid: string;
  doc_type: string;
  score: number;
};

export type DocumentPayload = {
  error: string;
  document: VerbaDocument;
};

export type NodePayload = {
  node_count: number;
  weaviate_version: string;
  nodes: NodeInfo[];
};

type NodeInfo = {
  status: string;
  shards: number;
  version: string;
  name: string;
};

type CollectionInfo = {
  name: string;
  count: number;
};

export type CollectionPayload = {
  collection_count: number;
  collections: CollectionInfo[];
};

export type MetadataPayload = {
  error: string;
  node_payload: NodePayload;
  collection_payload: CollectionPayload;
};

export type ChunksPayload = {
  error: string;
  chunks: VerbaChunk[];
};

export type ChunkPayload = {
  error: string;
  chunk: VerbaChunk;
};

export type ContentPayload = {
  error: string;
  content: ContentSnippet[];
  maxPage: number;
};

export type ContentSnippet = {
  content: string;
  chunk_id: number;
  score: number;
  type: "text" | "extract";
};

export type VectorsPayload = {
  error: string;
  vector_groups: {
    embedder: string;
    groups: VectorGroup[];
    dimensions: number;
  };
};

export type VerbaDocument = {
  title: string;
  metadata: string;
  extension: string;
  fileSize: number;
  labels: string[];
  source: string;
  meta: any;
};

export type VerbaChunk = {
  content: string;
  chunk_id: number;
  doc_uuid: string;
  pca: number[];
  umap: number[];
  start_i: number;
  end_i: number;
};

export type DocumentsPreviewPayload = {
  error: string;
  documents: DocumentPreview[];
  labels: string[];
  totalDocuments: number;
};

export type DocumentPreview = {
  title: string;
  uuid: string;
  labels: string[];
};

export type FormattedDocument = {
  beginning: string;
  substring: string;
  ending: string;
};

export type VectorGroup = {
  name: string;
  chunks: VectorChunk[];
};

export type VectorChunk = {
  vector: VerbaVector;
  chunk_id: string;
  uuid: string;
};

export type VerbaVector = {
  x: number;
  y: number;
  z: number;
};

export type DataCountPayload = {
  datacount: number;
};

export type Segment =
  | { type: "text"; content: string }
  | { type: "code"; language: string; content: string };

export interface Message {
  type: "user" | "system" | "error" | "retrieval";
  content: string | DocumentScore[];
  cached?: boolean;
  distance?: string;
  context?: string;
  runId?: string; // Make runId optional
}

// Setting Fields

export interface TextFieldSetting {
  type: "text";
  text: string;
  description: string;
}

export interface NumberFieldSetting {
  type: "number";
  value: number;
  description: string;
}

export interface ImageFieldSetting {
  type: "image";
  src: string;
  description: string;
}

export interface CheckboxSetting {
  type: "check";
  checked: boolean;
  description: string;
}

export interface ColorSetting {
  type: "color";
  color: string;
  description: string;
}

export interface SelectSetting {
  type: "select";
  options: string[];
  value: string;
  description: string;
}

// Base Settings

export interface Theme {
  theme_name: string;
  title: TextFieldSetting;
  subtitle: TextFieldSetting;
  intro_message: TextFieldSetting;
  image: ImageFieldSetting;
  primary_color: ColorSetting;
  secondary_color: ColorSetting;
  warning_color: ColorSetting;
  bg_color: ColorSetting;
  bg_alt_color: ColorSetting;
  text_color: ColorSetting;
  text_alt_color: ColorSetting;
  button_text_color: ColorSetting;
  button_text_alt_color: ColorSetting;
  button_color: ColorSetting;
  button_hover_color: ColorSetting;
  font: SelectSetting;
  theme: "light" | "dark";
}

export interface Themes {
  [key: string]: Theme;
}
declare module "bun:test" {
  interface Matchers<R> {
    toBeInTheDocument(): R;
    toBeDisabled(): R;
    toHaveClass(className: string): R;
    toHaveAttribute(attr: string, value?: string): R;
    toHaveTextContent(text: string): R;
    toHaveLength(length: number): R;
    toHaveBeenCalledWith(...args: any[]): R;
    toHaveBeenCalledTimes(times: number): R;
    toHaveBeenLastCalledWith(...args: any[]): R;
  }
} 

export type PageType =
  | "CHAT"
  | "DOCUMENTS"
  | "STATUS"
  | "IMPORT_DATA"
  | "SETTINGS"
  | "RAG"
  | "ADD";