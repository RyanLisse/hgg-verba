import { api } from "encore.dev/api";
import { QueryPayload } from "./types";

export const query = api(
  { method: "POST", path: "/api/query", expose: true },
  async (p: QueryPayload): Promise<{ error: string; documents: any[]; context: string }> => {
    // TODO: Port retrieval + embedding logic
    return { error: "", documents: [], context: "" };
  }
);