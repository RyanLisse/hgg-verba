import { describe, expect, test } from "bun:test";
import { render, within } from "@testing-library/react";
import ChatInterface from "../ChatInterface";
import { RAGConfig, Theme } from "@/app/types";

describe("ChatInterface", () => {
  test("renders chat interface correctly", () => {
    const mockConfig: RAGConfig = {
      Embedder: {
        selected: "OpenAIEmbeddings",
        components: {
          OpenAIEmbeddings: {
            config: {
              Model: {
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
              Model: {
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

    const mockTheme: Theme = {
      theme: "light",
      color: "#000000"
    };

    const { container } = render(
      <ChatInterface
        credentials={{
          url: "https://ydxeif3swakyvwjpke8q.c0.europe-west3.gcp.weaviate.cloud",
          username: "test",
          password: "test"
        }}
        setSelectedDocument={() => {}}
        setSelectedChunkScore={() => {}}
        currentPage="chat"
        RAGConfig={mockConfig}
        setRAGConfig={() => {}}
        selectedTheme={mockTheme}
        production="Local"
        addStatusMessage={() => {}}
        documentFilter={[]}
        setDocumentFilter={() => {}}
      />
    );

    // Check for essential elements
    const chatButton = within(container).getByRole("button", { name: /chat/i });
    const configButton = within(container).getByRole("button", { name: /config/i });
    
    expect(chatButton).toBeInTheDocument();
    expect(configButton).toBeInTheDocument();
  });
}); 