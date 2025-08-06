export interface Chunk {
  id: string;
  content: string;
  source: string;
  // biome-ignore lint/style/useNamingConvention: API response format
  start_index: number;
  // biome-ignore lint/style/useNamingConvention: API response format
  end_index: number;
  score: number;
}
