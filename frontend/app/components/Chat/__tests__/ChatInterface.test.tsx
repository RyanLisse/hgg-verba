import { describe, expect, test, vi, beforeEach } from "bun:test";
import { render, within, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ChatInterface from "../ChatInterface";
import { Theme, Credentials, RAGConfig, DocumentFilter, PageType } from "@/app/types";
import * as api from "@/app/api";

// Mock the WebSocket
class MockWebSocket {
  onopen: (() => void) | null = null;
  onmessage: ((event: any) => void) | null = null;
  onclose: ((event: any) => void) | null = null;
  onerror: ((error: any) => void) | null = null;
  readyState = WebSocket.OPEN;
  close = vi.fn();
  send = vi.fn();

  constructor(url: string) {}
}

// Mock the API functions
vi.mock("@/app/api", () => ({
  sendUserQuery: vi.fn(),
  fetchDatacount: vi.fn(),
  fetchRAGConfig: vi.fn(),
  fetchSuggestions: vi.fn(),
  fetchLabels: vi.fn(),
  updateRAGConfig: vi.fn(),
}));

describe("ChatInterface", () => {
  const mockTheme: Theme = {
    theme: "light",
    color: "#000000"
  };

  const mockCredentials: Credentials = {
    url: "http://localhost:8080",
    username: "test",
    password: "test"
  };

  const mockRAGConfig: RAGConfig = {
    Embedder: {
      selected: "OpenAIEmbeddings",
      components: {
        OpenAIEmbeddings: {
          config: {
            Model: {
              value: "text-embedding-ada-002",
              type: "string",
              values: ["text-embedding-ada-002"]
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
              value: "gpt-3.5-turbo",
              type: "string",
              values: ["gpt-3.5-turbo", "gpt-4"]
            }
          }
        }
      }
    }
  };

  const mockSetSelectedDocument = vi.fn();
  const mockSetSelectedChunkScore = vi.fn();
  const mockSetRAGConfig = vi.fn();
  const mockAddStatusMessage = vi.fn();
  const mockSetDocumentFilter = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    // @ts-ignore
    global.WebSocket = MockWebSocket;
  });

  test("renders chat interface with initial state", () => {
    const { container } = render(
      <ChatInterface
        credentials={mockCredentials}
        setSelectedDocument={mockSetSelectedDocument}
        setSelectedChunkScore={mockSetSelectedChunkScore}
        currentPage="chat"
        RAGConfig={mockRAGConfig}
        setRAGConfig={mockSetRAGConfig}
        selectedTheme={mockTheme}
        production="Local"
        addStatusMessage={mockAddStatusMessage}
        documentFilter={[]}
        setDocumentFilter={mockSetDocumentFilter}
      />
    );

    const chatInput = container.querySelector("textarea");
    expect(chatInput).toBeInTheDocument();
    expect(chatInput).toHaveValue("");
  });

  test("handles user input and message sending", async () => {
    const { container } = render(
      <ChatInterface
        credentials={mockCredentials}
        setSelectedDocument={mockSetSelectedDocument}
        setSelectedChunkScore={mockSetSelectedChunkScore}
        currentPage="chat"
        RAGConfig={mockRAGConfig}
        setRAGConfig={mockSetRAGConfig}
        selectedTheme={mockTheme}
        production="Local"
        addStatusMessage={mockAddStatusMessage}
        documentFilter={[]}
        setDocumentFilter={mockSetDocumentFilter}
      />
    );

    const chatInput = container.querySelector("textarea")!;
    await userEvent.type(chatInput, "Hello, world!");
    expect(chatInput).toHaveValue("Hello, world!");

    const sendButton = within(container).getByRole("button", { name: /send/i });
    await userEvent.click(sendButton);

    expect(api.sendUserQuery).toHaveBeenCalledWith(
      "Hello, world!",
      mockRAGConfig,
      [],
      [],
      mockCredentials
    );
  });

  test("displays error message on API failure", async () => {
    (api.sendUserQuery as jest.Mock).mockRejectedValueOnce(new Error("API Error"));

    const { container } = render(
      <ChatInterface
        credentials={mockCredentials}
        setSelectedDocument={mockSetSelectedDocument}
        setSelectedChunkScore={mockSetSelectedChunkScore}
        currentPage="chat"
        RAGConfig={mockRAGConfig}
        setRAGConfig={mockSetRAGConfig}
        selectedTheme={mockTheme}
        production="Local"
        addStatusMessage={mockAddStatusMessage}
        documentFilter={[]}
        setDocumentFilter={mockSetDocumentFilter}
      />
    );

    const chatInput = container.querySelector("textarea")!;
    await userEvent.type(chatInput, "Hello, world!");
    const sendButton = within(container).getByRole("button", { name: /send/i });
    await userEvent.click(sendButton);

    expect(mockAddStatusMessage).toHaveBeenCalledWith(
      "Failed to fetch from API",
      "ERROR"
    );
  });

  test("handles WebSocket connection status", async () => {
    const { container } = render(
      <ChatInterface
        credentials={mockCredentials}
        setSelectedDocument={mockSetSelectedDocument}
        setSelectedChunkScore={mockSetSelectedChunkScore}
        currentPage="chat"
        RAGConfig={mockRAGConfig}
        setRAGConfig={mockSetRAGConfig}
        selectedTheme={mockTheme}
        production="Local"
        addStatusMessage={mockAddStatusMessage}
        documentFilter={[]}
        setDocumentFilter={mockSetDocumentFilter}
      />
    );

    // WebSocket connection should be established
    const statusLabel = within(container).getByText(/online/i);
    expect(statusLabel).toBeInTheDocument();
  });

  test("handles settings toggle", async () => {
    const { container } = render(
      <ChatInterface
        credentials={mockCredentials}
        setSelectedDocument={mockSetSelectedDocument}
        setSelectedChunkScore={mockSetSelectedChunkScore}
        currentPage="chat"
        RAGConfig={mockRAGConfig}
        setRAGConfig={mockSetRAGConfig}
        selectedTheme={mockTheme}
        production="Local"
        addStatusMessage={mockAddStatusMessage}
        documentFilter={[]}
        setDocumentFilter={mockSetDocumentFilter}
      />
    );

    const settingsButton = within(container).getByTitle(/settings/i);
    await userEvent.click(settingsButton);

    const chatConfigComponent = container.querySelector(".flex.flex-col.justify-start.rounded-2xl.w-full.p-4");
    expect(chatConfigComponent).toBeInTheDocument();
  });

  test("handles feedback submission", async () => {
    const { container } = render(
      <ChatInterface
        credentials={mockCredentials}
        setSelectedDocument={mockSetSelectedDocument}
        setSelectedChunkScore={mockSetSelectedChunkScore}
        currentPage="chat"
        RAGConfig={mockRAGConfig}
        setRAGConfig={mockSetRAGConfig}
        selectedTheme={mockTheme}
        production="Local"
        addStatusMessage={mockAddStatusMessage}
        documentFilter={[]}
        setDocumentFilter={mockSetDocumentFilter}
      />
    );

    // Simulate receiving a message with a runId
    const mockMessage = {
      message: "Test message",
      finish_reason: "stop",
      full_text: "Test message",
      runId: "test-run-id"
    };

    act(() => {
      const ws = global.WebSocket as any;
      const instance = ws.mock.instances[0];
      instance.onmessage?.({ data: JSON.stringify(mockMessage) });
    });

    // Find and click the feedback button
    const feedbackButton = within(container).getByRole("button", { name: /feedback/i });
    await userEvent.click(feedbackButton);

    // Find and click the positive feedback button
    const positiveButton = within(container).getByRole("button", { name: /yes/i });
    await userEvent.click(positiveButton);

    expect(mockAddStatusMessage).toHaveBeenCalledWith(
      expect.stringContaining("Submitting feedback"),
      "INFO"
    );
  });

  test("handles reconnection", async () => {
    const { container } = render(
      <ChatInterface
        credentials={mockCredentials}
        setSelectedDocument={mockSetSelectedDocument}
        setSelectedChunkScore={mockSetSelectedChunkScore}
        currentPage="chat"
        RAGConfig={mockRAGConfig}
        setRAGConfig={mockSetRAGConfig}
        selectedTheme={mockTheme}
        production="Local"
        addStatusMessage={mockAddStatusMessage}
        documentFilter={[]}
        setDocumentFilter={mockSetDocumentFilter}
      />
    );

    const reconnectButton = within(container).getByTitle(/reconnect/i);
    await userEvent.click(reconnectButton);

    expect(mockAddStatusMessage).toHaveBeenCalledWith(
      "Reconnecting to Verba...",
      "INFO"
    );
  });
}); 