import { api } from "encore.dev/api";
import { db } from "./db";
import { DeleteSuggestionPayload, GetAllSuggestionsPayload, GetSuggestionsPayload } from "./types";

export const get_suggestions = api(
  { method: "POST", path: "/api/get_suggestions", expose: true },
  async (p: GetSuggestionsPayload): Promise<{ suggestions: any[] }> => {
    const rows = await db.query`
      SELECT uuid, query, count FROM verba_suggestions
      WHERE query ILIKE ${'%' + p.query + '%'}
      ORDER BY count DESC
      LIMIT ${p.limit}
    `;
    return { suggestions: rows ?? [] };
  }
);

export const get_all_suggestions = api(
  { method: "POST", path: "/api/get_all_suggestions", expose: true },
  async (p: GetAllSuggestionsPayload): Promise<{ suggestions: any[]; total_count: number }> => {
    const offset = (p.page - 1) * p.pageSize;
    const rows = await db.query`
      SELECT uuid, query, count FROM verba_suggestions ORDER BY updated_at DESC LIMIT ${p.pageSize} OFFSET ${offset}
    `;
    const countRow = await db.queryRow`SELECT COUNT(*)::int as c FROM verba_suggestions`;
    return { suggestions: rows ?? [], total_count: countRow?.c ?? 0 };
  }
);

export const delete_suggestion = api(
  { method: "POST", path: "/api/delete_suggestion", expose: true },
  async (p: DeleteSuggestionPayload): Promise<{ status: number }> => {
    await db.exec`DELETE FROM verba_suggestions WHERE uuid = ${p.uuid}`;
    return { status: 200 };
  }
);