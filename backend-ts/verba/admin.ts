import { api } from "encore.dev/api";
import { db } from "./db";
import { Credentials, ResetPayload } from "./types";

export const reset = api(
  { method: "POST", path: "/api/reset", expose: true },
  async (p: ResetPayload): Promise<{}> => {
    if (p.resetMode === "ALL") {
      await db.exec`TRUNCATE TABLE verba_chunks, verba_documents, verba_suggestions, verba_config RESTART IDENTITY CASCADE`;
    } else if (p.resetMode === "DOCUMENTS") {
      await db.exec`TRUNCATE TABLE verba_chunks, verba_documents RESTART IDENTITY CASCADE`;
    } else if (p.resetMode === "CONFIG") {
      await db.exec`TRUNCATE TABLE verba_config RESTART IDENTITY CASCADE`;
    } else if (p.resetMode === "SUGGESTIONS") {
      await db.exec`TRUNCATE TABLE verba_suggestions RESTART IDENTITY CASCADE`;
    }
    return {};
  }
);

export const get_meta = api(
  { method: "POST", path: "/api/get_meta", expose: true },
  async (_: Credentials): Promise<{ error: string; node_payload: any; collection_payload: any }> => {
    const docCount = await db.queryRow`SELECT COUNT(*)::int as c FROM verba_documents`;
    const chunkCount = await db.queryRow`SELECT COUNT(*)::int as c FROM verba_chunks`;
    return {
      error: "",
      node_payload: { documents: docCount?.c ?? 0 },
      collection_payload: { chunks: chunkCount?.c ?? 0 },
    };
  }
);