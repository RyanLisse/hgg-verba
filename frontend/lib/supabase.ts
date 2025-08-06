import { createClient } from "@supabase/supabase-js";
import type { Database } from "./database.types";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

export const supabase = createClient<Database>(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
  },
});

// Helper functions for vector operations
export async function searchDocuments(
  queryEmbedding: number[],
  limit: number = 10,
  threshold: number = 0.7
) {
  const { data, error } = await supabase.rpc("search_similar_chunks", {
    query_embedding: queryEmbedding,
    match_count: limit,
    match_threshold: threshold,
  });

  if (error) throw error;
  return data;
}

export async function hybridSearch(
  queryText: string,
  queryEmbedding: number[],
  limit: number = 10,
  alpha: number = 0.5
) {
  const { data, error } = await supabase.rpc("hybrid_search_chunks", {
    query_text: queryText,
    query_embedding: queryEmbedding,
    match_count: limit,
    alpha: alpha,
  });

  if (error) throw error;
  return data;
}

export async function getDocuments(status?: string, limit: number = 100, offset: number = 0) {
  let query = supabase
    .from("documents")
    .select("*")
    .order("created_at", { ascending: false })
    .range(offset, offset + limit - 1);

  if (status) {
    query = query.eq("status", status);
  }

  const { data, error } = await query;
  if (error) throw error;
  return data;
}

export async function deleteDocument(documentId: string) {
  const { error } = await supabase.from("documents").delete().eq("id", documentId);
  if (error) throw error;
  return true;
}

export async function createConversation(title?: string) {
  const { data, error } = await supabase
    .from("conversations")
    .insert({ title: title || "New Conversation" })
    .select()
    .single();

  if (error) throw error;
  return data;
}

export async function addMessage(
  conversationId: string,
  role: "user" | "assistant" | "system",
  content: string,
  chunkIds?: string[]
) {
  const { data, error } = await supabase
    .from("messages")
    .insert({
      conversation_id: conversationId,
      role,
      content,
      chunk_ids: chunkIds || [],
    })
    .select()
    .single();

  if (error) throw error;
  return data;
}

export async function getConversationMessages(conversationId: string) {
  const { data, error } = await supabase
    .from("messages")
    .select("*")
    .eq("conversation_id", conversationId)
    .order("created_at", { ascending: true });

  if (error) throw error;
  return data;
}

export async function getSuggestions(prefix: string, limit: number = 10) {
  const { data, error } = await supabase
    .from("query_suggestions")
    .select("query")
    .ilike("query", `${prefix}%`)
    .order("frequency", { ascending: false })
    .limit(limit);

  if (error) throw error;
  return data?.map((item) => item.query) || [];
}