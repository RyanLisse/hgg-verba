export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[];

export interface Database {
  public: {
    Tables: {
      documents: {
        Row: {
          id: string;
          name: string;
          type: "PDF" | "TXT" | "HTML" | "MARKDOWN" | "DOCX" | "CSV" | "JSON";
          status: "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";
          path: string | null;
          content: string | null;
          metadata: Json;
          file_size: number | null;
          total_chunks: number;
          created_at: string;
          updated_at: string;
          created_by: string | null;
        };
        Insert: {
          id?: string;
          name: string;
          type: "PDF" | "TXT" | "HTML" | "MARKDOWN" | "DOCX" | "CSV" | "JSON";
          status?: "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";
          path?: string | null;
          content?: string | null;
          metadata?: Json;
          file_size?: number | null;
          total_chunks?: number;
          created_at?: string;
          updated_at?: string;
          created_by?: string | null;
        };
        Update: {
          id?: string;
          name?: string;
          type?: "PDF" | "TXT" | "HTML" | "MARKDOWN" | "DOCX" | "CSV" | "JSON";
          status?: "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";
          path?: string | null;
          content?: string | null;
          metadata?: Json;
          file_size?: number | null;
          total_chunks?: number;
          created_at?: string;
          updated_at?: string;
          created_by?: string | null;
        };
      };
      document_chunks: {
        Row: {
          id: string;
          document_id: string;
          chunk_index: number;
          chunk_type: "TEXT" | "TABLE" | "IMAGE" | "CODE";
          content: string;
          metadata: Json;
          token_count: number | null;
          embedding: number[] | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          document_id: string;
          chunk_index: number;
          chunk_type?: "TEXT" | "TABLE" | "IMAGE" | "CODE";
          content: string;
          metadata?: Json;
          token_count?: number | null;
          embedding?: number[] | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          document_id?: string;
          chunk_index?: number;
          chunk_type?: "TEXT" | "TABLE" | "IMAGE" | "CODE";
          content?: string;
          metadata?: Json;
          token_count?: number | null;
          embedding?: number[] | null;
          created_at?: string;
          updated_at?: string;
        };
      };
      configurations: {
        Row: {
          id: string;
          config_type: string;
          config_name: string;
          config_data: Json;
          is_active: boolean;
          created_at: string;
          updated_at: string;
          created_by: string | null;
        };
        Insert: {
          id?: string;
          config_type: string;
          config_name: string;
          config_data: Json;
          is_active?: boolean;
          created_at?: string;
          updated_at?: string;
          created_by?: string | null;
        };
        Update: {
          id?: string;
          config_type?: string;
          config_name?: string;
          config_data?: Json;
          is_active?: boolean;
          created_at?: string;
          updated_at?: string;
          created_by?: string | null;
        };
      };
      query_suggestions: {
        Row: {
          id: string;
          query: string;
          frequency: number;
          last_used: string;
          metadata: Json;
          created_at: string;
        };
        Insert: {
          id?: string;
          query: string;
          frequency?: number;
          last_used?: string;
          metadata?: Json;
          created_at?: string;
        };
        Update: {
          id?: string;
          query?: string;
          frequency?: number;
          last_used?: string;
          metadata?: Json;
          created_at?: string;
        };
      };
      semantic_cache: {
        Row: {
          id: string;
          query: string;
          query_embedding: number[] | null;
          response: string;
          metadata: Json;
          hit_count: number;
          last_accessed: string;
          created_at: string;
          expires_at: string;
        };
        Insert: {
          id?: string;
          query: string;
          query_embedding?: number[] | null;
          response: string;
          metadata?: Json;
          hit_count?: number;
          last_accessed?: string;
          created_at?: string;
          expires_at?: string;
        };
        Update: {
          id?: string;
          query?: string;
          query_embedding?: number[] | null;
          response?: string;
          metadata?: Json;
          hit_count?: number;
          last_accessed?: string;
          created_at?: string;
          expires_at?: string;
        };
      };
      conversations: {
        Row: {
          id: string;
          title: string | null;
          metadata: Json;
          created_at: string;
          updated_at: string;
          user_id: string | null;
        };
        Insert: {
          id?: string;
          title?: string | null;
          metadata?: Json;
          created_at?: string;
          updated_at?: string;
          user_id?: string | null;
        };
        Update: {
          id?: string;
          title?: string | null;
          metadata?: Json;
          created_at?: string;
          updated_at?: string;
          user_id?: string | null;
        };
      };
      messages: {
        Row: {
          id: string;
          conversation_id: string;
          role: "user" | "assistant" | "system";
          content: string;
          metadata: Json;
          chunk_ids: string[];
          created_at: string;
        };
        Insert: {
          id?: string;
          conversation_id: string;
          role: "user" | "assistant" | "system";
          content: string;
          metadata?: Json;
          chunk_ids?: string[];
          created_at?: string;
        };
        Update: {
          id?: string;
          conversation_id?: string;
          role?: "user" | "assistant" | "system";
          content?: string;
          metadata?: Json;
          chunk_ids?: string[];
          created_at?: string;
        };
      };
      embedder_configs: {
        Row: {
          id: string;
          name: string;
          model_name: string;
          dimensions: number;
          config: Json;
          is_active: boolean;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          name: string;
          model_name: string;
          dimensions: number;
          config: Json;
          is_active?: boolean;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          name?: string;
          model_name?: string;
          dimensions?: number;
          config?: Json;
          is_active?: boolean;
          created_at?: string;
          updated_at?: string;
        };
      };
    };
    Views: {
      [_ in never]: never;
    };
    Functions: {
      search_similar_chunks: {
        Args: {
          query_embedding: number[];
          match_count?: number;
          match_threshold?: number;
        };
        Returns: {
          id: string;
          document_id: string;
          content: string;
          metadata: Json;
          similarity: number;
        }[];
      };
      hybrid_search_chunks: {
        Args: {
          query_text: string;
          query_embedding: number[];
          match_count?: number;
          alpha?: number;
        };
        Returns: {
          id: string;
          document_id: string;
          content: string;
          metadata: Json;
          score: number;
        }[];
      };
    };
    Enums: {
      document_type: "PDF" | "TXT" | "HTML" | "MARKDOWN" | "DOCX" | "CSV" | "JSON";
      document_status: "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";
      chunk_type: "TEXT" | "TABLE" | "IMAGE" | "CODE";
    };
  };
}