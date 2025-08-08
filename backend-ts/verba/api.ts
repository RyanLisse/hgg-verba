import { api } from "encore.dev/api";
import { HealthResponse, ConnectPayload } from "./types";

export const health = api(
  { method: "GET", path: "/api/health", expose: true },
  async (): Promise<HealthResponse> => {
    return {
      message: "Alive!",
      production: process.env.VERBA_PRODUCTION || "Local",
      gtag: process.env.VERBA_GOOGLE_TAG || "",
      deployments: {
        DATABASE_URL: process.env.DATABASE_URL || "",
        POSTGRES_HOST: process.env.POSTGRES_HOST || "",
        POSTGRES_PASSWORD: process.env.POSTGRES_PASSWORD || "",
      },
    };
  }
);

export const connect = api(
  { method: "POST", path: "/api/connect", expose: true },
  async (p: ConnectPayload): Promise<{ connected: boolean; error: string }> => {
    // TODO: Implement actual connection pooling and config loading
    const hasUrl = Boolean(p.credentials?.url);
    return { connected: hasUrl, error: hasUrl ? "" : "No database URL provided" };
  }
);