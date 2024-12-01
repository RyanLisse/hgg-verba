import { describe, expect, test } from "bun:test";
import { render } from "@testing-library/react";
import ChatConfig from "../ChatConfig";
import { RAGConfig } from "@/app/types";

describe("ChatConfig", () => {
  test("renders config form correctly", () => {
    const mockConfig: RAGConfig = {
      Embedder: {
        selected: "OpenAIEmbeddings",
        components: {
          OpenAIEmbeddings: {
            config: {
              model: {
                value: "text-embedding-3-large",
                type: "string",
                values: ["text-embedding-3-large"]
              }
            }
          }
        }
      },
      Generator: {
        selected: "ChatOpenAI",
        components: {
          ChatOpenAI: {
            config: {
              model: {
                value: "gpt-4o-mini",
                type: "string",
                values: ["gpt-4o-mini", "gpt-4"]
              }
            }
          }
        }
      },
      Retriever: {
        selected: "MultiQueryRetriever",
        components: {
          MultiQueryRetriever: {
            config: {
              search_type: {
                value: "similarity",
                type: "string",
                values: ["similarity", "mmr"]
              }
            }
          }
        }
      }
    };

    const { container } = render(
      <ChatConfig
        RAGConfig={mockConfig}
        setRAGConfig={() => {}}
        onSave={() => {}}
        onReset={() => {}}
        addStatusMessage={() => {}}
        credentials={{
          url: "https://ydxeif3swakyvwjpke8q.c0.europe-west3.gcp.weaviate.cloud",
          username: "test",
          password: "test"
        }}
        production="Local"
      />
    );

    const configContainer = container.querySelector(".flex.flex-col.justify-start.rounded-2xl.w-full.p-4");
    expect(configContainer).toBeInTheDocument();
  });
}); 