import { api } from "encore.dev/api";
import { db } from "./db";
import { ChunksPayload, DatacountPayload, GetChunkPayload, GetContentPayload, GetDocumentPayload, GetVectorPayload, SearchQueryPayload, Credentials } from "./types";

export const get_document = api(
  { method: "POST", path: "/api/get_document", expose: true },
  async (p: GetDocumentPayload): Promise<{ error: string; document: any | null }> => {
    const row = await db.queryRow`
      SELECT uuid, title, extension, file_size as "fileSize", labels, source, meta, metadata
      FROM verba_documents WHERE uuid = ${p.uuid}
    `;
    if (!row) return { error: "Couldn't retrieve requested document", document: null };
    return { error: "", document: { ...row, content: "" } };
  }
);

export const get_datacount = api(
  { method: "POST", path: "/api/get_datacount", expose: true },
  async (p: DatacountPayload): Promise<{ datacount: number }> => {
    const row = await db.queryRow`
      SELECT COUNT(*)::int as c FROM verba_chunks
    `;
    return { datacount: row?.c ?? 0 };
  }
);

export const get_labels = api(
  { method: "POST", path: "/api/get_labels", expose: true },
  async (_: Credentials): Promise<{ labels: string[] }> => {
    const rows = await db.query`
      SELECT DISTINCT unnest(labels) as label FROM verba_documents WHERE labels IS NOT NULL
    `;
    const labels = rows?.map((r: any) => r.label).filter(Boolean) ?? [];
    return { labels };
  }
);

export const get_content = api(
  { method: "POST", path: "/api/get_content", expose: true },
  async (p: GetContentPayload): Promise<{ error: string; content: any[]; maxPage: number }> => {
    const pageSize = 50;
    const offset = (p.page - 1) * pageSize;
    const rows = await db.query`
      SELECT uuid, chunk_id, content FROM verba_chunks
      WHERE document_uuid = ${p.uuid}
      ORDER BY chunk_id ASC
      LIMIT ${pageSize} OFFSET ${offset}
    `;
    const countRow = await db.queryRow`
      SELECT CEIL(COUNT(*)::decimal / ${pageSize})::int as pages FROM verba_chunks WHERE document_uuid = ${p.uuid}
    `;
    return { error: "", content: rows ?? [], maxPage: countRow?.pages ?? 1 };
  }
);

export const get_vectors = api(
  { method: "POST", path: "/api/get_vectors", expose: true },
  async (p: GetVectorPayload): Promise<{ error: string; vector_groups: any[] }> => {
    const rows = await db.query`
      SELECT chunk_id, embedder FROM verba_chunks WHERE document_uuid = ${p.uuid}
    `;
    return { error: "", vector_groups: rows ?? [] };
  }
);

export const get_chunks = api(
  { method: "POST", path: "/api/get_chunks", expose: true },
  async (p: ChunksPayload): Promise<{ error: string; chunks: any[] | null }> => {
    const page = p.page;
    const pageSize = p.pageSize;
    const offset = (page - 1) * pageSize;
    const rows = await db.query`
      SELECT uuid, chunk_id, content FROM verba_chunks
      WHERE document_uuid = ${p.uuid}
      ORDER BY chunk_id ASC
      LIMIT ${pageSize} OFFSET ${offset}
    `;
    return { error: "", chunks: rows ?? [] };
  }
);

export const get_chunk = api(
  { method: "POST", path: "/api/get_chunk", expose: true },
  async (p: GetChunkPayload): Promise<{ error: string; chunk: any | null }> => {
    const row = await db.queryRow`
      SELECT uuid, chunk_id, content FROM verba_chunks WHERE uuid = ${p.uuid}
    `;
    return { error: row ? "" : "Not found", chunk: row ?? null };
  }
);

export const get_all_documents = api(
  { method: "POST", path: "/api/get_all_documents", expose: true },
  async (p: SearchQueryPayload): Promise<{ documents: any[]; labels: string[]; error: string; totalDocuments: number }> => {
    const page = p.page;
    const pageSize = p.pageSize;
    const offset = (page - 1) * pageSize;
    const rows = await db.query`
      SELECT uuid, title, extension, file_size as "fileSize", labels, source, meta
      FROM verba_documents
      WHERE (${'%' + p.query + '%'} = '%%' OR title ILIKE ${'%' + p.query + '%'})
      ORDER BY updated_at DESC
      LIMIT ${pageSize} OFFSET ${offset}
    `;
    const countRow = await db.queryRow`
      SELECT COUNT(*)::int as c FROM verba_documents WHERE (${'%' + p.query + '%'} = '%%' OR title ILIKE ${'%' + p.query + '%'})
    `;
    const labelRows = await db.query`SELECT DISTINCT unnest(labels) as label FROM verba_documents WHERE labels IS NOT NULL`;
    const labels = labelRows?.map((r: any) => r.label).filter(Boolean) ?? [];
    return { documents: rows ?? [], labels, error: "", totalDocuments: countRow?.c ?? 0 };
  }
);

export const delete_document = api(
  { method: "POST", path: "/api/delete_document", expose: true },
  async (p: GetDocumentPayload): Promise<{}> => {
    await db.exec`DELETE FROM verba_documents WHERE uuid = ${p.uuid}`;
    return {};
  }
);