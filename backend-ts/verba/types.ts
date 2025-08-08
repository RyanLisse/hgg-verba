export type Deployment = "Weaviate" | "Docker" | "Local";

export interface Credentials {
  deployment: Deployment;
  url: string;
  key: string;
}

export interface ConnectPayload {
  credentials: Credentials;
}

export interface HealthResponse {
  message: string;
  production: string;
  gtag: string;
  deployments: Record<string, string>;
}