import { api } from "encore.dev/api";
import { db } from "./db";
import { Credentials, RAGConfig, SetRAGConfigPayload, SetUserConfigPayload, SetThemeConfigPayload } from "./types";

async function upsertConfig(configType: string, data: unknown): Promise<void> {
  await db.exec`
    INSERT INTO verba_config (config_type, config)
    VALUES (${configType}, ${JSON.stringify(data)}::jsonb)
    ON CONFLICT (uuid) DO NOTHING
  `;
  // We keep one row per type; simplest is delete others then insert
}

export const get_rag_config = api(
  { method: "POST", path: "/api/get_rag_config", expose: true },
  async (p: Credentials): Promise<{ rag_config: RAGConfig | {}; error: string }> => {
    const row = await db.queryRow`
      SELECT config FROM verba_config WHERE config_type = 'rag' ORDER BY updated_at DESC LIMIT 1
    `;
    return { rag_config: (row?.config as RAGConfig) ?? ({} as any), error: "" };
  }
);

export const set_rag_config = api(
  { method: "POST", path: "/api/set_rag_config", expose: true },
  async (p: SetRAGConfigPayload): Promise<{ status: number }> => {
    await db.exec`
      INSERT INTO verba_config (config_type, config)
      VALUES ('rag', ${JSON.stringify(p.rag_config)}::jsonb)
    `;
    return { status: 200 };
  }
);

export const get_user_config = api(
  { method: "POST", path: "/api/get_user_config", expose: true },
  async (p: Credentials): Promise<{ user_config: Record<string, unknown> | {}; error: string }> => {
    const row = await db.queryRow`
      SELECT config FROM verba_config WHERE config_type = 'user' ORDER BY updated_at DESC LIMIT 1
    `;
    return { user_config: (row?.config as any) ?? {}, error: "" };
  }
);

export const set_user_config = api(
  { method: "POST", path: "/api/set_user_config", expose: true },
  async (p: SetUserConfigPayload): Promise<{ status: number; status_msg: string }> => {
    await db.exec`
      INSERT INTO verba_config (config_type, config)
      VALUES ('user', ${JSON.stringify(p.user_config)}::jsonb)
    `;
    return { status: 200, status_msg: "User config updated" };
  }
);

export const get_theme_config = api(
  { method: "POST", path: "/api/get_theme_config", expose: true },
  async (p: Credentials): Promise<{ theme: any; themes: any; error: string }> => {
    const row = await db.queryRow`
      SELECT config FROM verba_config WHERE config_type = 'theme' ORDER BY updated_at DESC LIMIT 1
    `;
    const themeConfig = (row?.config as any) ?? {};
    return { theme: themeConfig?.theme ?? {}, themes: themeConfig?.themes ?? {}, error: "" };
  }
);

export const set_theme_config = api(
  { method: "POST", path: "/api/set_theme_config", expose: true },
  async (p: SetThemeConfigPayload): Promise<{ status: number }> => {
    await db.exec`
      INSERT INTO verba_config (config_type, config)
      VALUES ('theme', ${JSON.stringify({ theme: p.theme, themes: p.themes })}::jsonb)
    `;
    return { status: 200 };
  }
);