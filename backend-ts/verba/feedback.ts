import { api } from "encore.dev/api";
import { FeedbackPayload } from "./types";

export const feedback = api(
  { method: "POST", path: "/api/feedback", expose: true },
  async (_: FeedbackPayload): Promise<{ status: string }> => {
    return { status: "success" };
  }
);