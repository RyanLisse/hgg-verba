export interface Chunk {
  id: string;
  content: string;
  source: string;
  start_index: number;
  end_index: number;
  score: number;
}