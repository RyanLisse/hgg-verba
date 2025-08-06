import { describe, expect, test } from "bun:test";
import type { PageType, RAGConfig, Theme } from "@/app/types";
import { render, within } from "@testing-library/react";
import ChatInterface from "../ChatInterface";

describe("ChatInterface", () => {
  test("renders chat interface correctly", () => {
    const mockConfig: RAGConfig = {
      Embedder: {
        selected: "OpenAIEmbeddings",
        components: {
          OpenAIEmbeddings: {
            name: "OpenAI Embeddings",
            library: ["@langchain/openai"],
            description: ["OpenAI's text embedding models"],
            variables: [],
            type: "embedder",
            selected: true,
            available: true,
            config: {
              Model: {
                value: "text-embedding-3-large",
                type: "string",
                values: ["text-embedding-3-large"],
                description: "The model to use for embeddings",
              },
            },
          },
        },
      },
      Generator: {
        selected: "ChatOpenAI",
        components: {
          ChatOpenAI: {
            name: "ChatOpenAI",
            library: ["@langchain/openai"],
            description: ["OpenAI's chat completion models"],
            variables: [],
            type: "generator",
            selected: true,
            available: true,
            config: {
              Model: {
                value: "gpt-4o-mini",
                type: "string",
                values: ["gpt-4o-mini", "gpt-4"],
                description: "The model to use for chat completion",
              },
            },
          },
        },
      },
      Retriever: {
        selected: "MultiQueryRetriever",
        components: {
          MultiQueryRetriever: {
            name: "Multi Query Retriever",
            library: ["@langchain/core"],
            description: ["Retriever that generates multiple queries"],
            variables: [],
            type: "retriever",
            selected: true,
            available: true,
            config: {
              search_type: {
                value: "similarity",
                type: "string",
                values: ["similarity", "mmr"],
                description: "The type of search to perform",
              },
            },
          },
        },
      },
    };

    const mockTheme: Theme = {
      theme_name: "light",
      title: {
        text: "Test Title",
        type: "text",
        description: "Test title description",
      },
      subtitle: {
        text: "Test Subtitle",
        type: "text",
        description: "Test subtitle description",
      },
      intro_message: {
        text: "Test Intro",
        type: "text",
        description: "Test intro description",
      },
      image: {
        src: "test-image.png",
        type: "image",
        description: "Test image description",
      },
      primary_color: {
        color: "#000000",
        type: "color",
        description: "Primary color",
      },
      secondary_color: {
        color: "#ffffff",
        type: "color",
        description: "Secondary color",
      },
      warning_color: {
        color: "#ff0000",
        type: "color",
        description: "Warning color",
      },
      bg_color: {
        color: "#ffffff",
        type: "color",
        description: "Background color",
      },
      bg_alt_color: {
        color: "#f0f0f0",
        type: "color",
        description: "Alternate background color",
      },
      text_color: {
        color: "#111111",
        type: "color",
        description: "Text color",
      },
      text_alt_color: {
        color: "#222222",
        type: "color",
        description: "Alternate text color",
      },
      button_text_color: {
        color: "#333333",
        type: "color",
        description: "Button text color",
      },
      button_text_alt_color: {
        color: "#444444",
        type: "color",
        description: "Alternate button text color",
      },
      button_color: {
        color: "#555555",
        type: "color",
        description: "Button color",
      },
      button_hover_color: {
        color: "#666666",
        type: "color",
        description: "Button hover color",
      },
      font: {
        type: "select",
        value: "Open_Sans",
        description: "Text Font",
        options: ["Inter", "Plus_Jakarta_Sans", "Open_Sans", "PT_Mono"],
      },
      theme: "light",
    };

    const mockProps = {
      credentials: {
        url: "https://test.com",
        deployment: "Local" as const,
        key: "test-key",
      },
      setSelectedDocument: () => {
        // Test stub: intentionally empty for mock purposes
      },
      setSelectedChunkScore: () => {
        // Test stub: intentionally empty for mock purposes
      },
      currentPage: "CHAT" as PageType,
      ragConfig: mockConfig,
      setRAGConfig: () => {
        // Test stub: intentionally empty for mock purposes
      },
      selectedTheme: mockTheme,
      production: "Local" as const,
      addStatusMessage: () => {
        // Test stub: intentionally empty for mock purposes
      },
      documentFilter: [],
      setDocumentFilter: () => {
        // Test stub: intentionally empty for mock purposes
      },
      labels: ["Label1", "Label2", "Label3"],
      filterLabels: [],
      setFilterLabels: () => {
        // Test stub: intentionally empty for mock purposes
      },
    };

    const { container } = render(<ChatInterface {...mockProps} />);

    // Check for essential elements
    const chatButton = within(container).getByRole("button", { name: /chat/i });
    const configButton = within(container).getByRole("button", {
      name: /config/i,
    });

    expect(chatButton).toBeInTheDocument();
    expect(configButton).toBeInTheDocument();
  });
});
