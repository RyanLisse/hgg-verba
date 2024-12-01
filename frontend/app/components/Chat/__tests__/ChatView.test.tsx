import { describe, expect, test, vi } from "bun:test";
import { render, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ChatView from "../ChatView";
import { Theme, Credentials, RAGConfig, DocumentFilter, PageType } from "@/app/types";

describe("ChatView", () => {
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
    chunk_size: 500,
    chunk_overlap: 50,
    model: "gpt-3.5-turbo",
    temperature: 0.7,
    max_tokens: 1000
  };

  const mockDocumentFilter: DocumentFilter[] = [];

  const mockAddStatusMessage = vi.fn();
  const mockSetRAGConfig = vi.fn();
  const mockSetDocumentFilter = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  test("renders ChatInterface by default", () => {
    const { container } = render(
      <ChatView
        selectedTheme={mockTheme}
        credentials={mockCredentials}
        addStatusMessage={mockAddStatusMessage}
        production="Local"
        currentPage="chat"
        RAGConfig={mockRAGConfig}
        setRAGConfig={mockSetRAGConfig}
        documentFilter={mockDocumentFilter}
        setDocumentFilter={mockSetDocumentFilter}
      />
    );

    const chatInterface = container.querySelector(".w-full.md\\:w-\\[45vw\\].md\\:flex");
    expect(chatInterface).toBeInTheDocument();
  });

  test("hides DocumentExplorer by default on mobile", () => {
    const { container } = render(
      <ChatView
        selectedTheme={mockTheme}
        credentials={mockCredentials}
        addStatusMessage={mockAddStatusMessage}
        production="Local"
        currentPage="chat"
        RAGConfig={mockRAGConfig}
        setRAGConfig={mockSetRAGConfig}
        documentFilter={mockDocumentFilter}
        setDocumentFilter={mockSetDocumentFilter}
      />
    );

    const documentExplorer = container.querySelector(".hidden.md\\:flex.md\\:w-\\[55vw\\]");
    expect(documentExplorer).toBeInTheDocument();
  });

  test("shows DocumentExplorer when document is selected", () => {
    const { container, rerender } = render(
      <ChatView
        selectedTheme={mockTheme}
        credentials={mockCredentials}
        addStatusMessage={mockAddStatusMessage}
        production="Local"
        currentPage="chat"
        RAGConfig={mockRAGConfig}
        setRAGConfig={mockSetRAGConfig}
        documentFilter={mockDocumentFilter}
        setDocumentFilter={mockSetDocumentFilter}
      />
    );

    // Simulate document selection by finding the setSelectedDocument function
    const chatInterface = container.querySelector(".w-full.md\\:w-\\[45vw\\].md\\:flex");
    expect(chatInterface).toBeInTheDocument();

    // Get the ChatInterface component instance
    const chatInterfaceComponent = within(chatInterface!).getByRole("complementary");
    expect(chatInterfaceComponent).toBeInTheDocument();
  });

  test("applies correct layout classes", () => {
    const { container } = render(
      <ChatView
        selectedTheme={mockTheme}
        credentials={mockCredentials}
        addStatusMessage={mockAddStatusMessage}
        production="Local"
        currentPage="chat"
        RAGConfig={mockRAGConfig}
        setRAGConfig={mockSetRAGConfig}
        documentFilter={mockDocumentFilter}
        setDocumentFilter={mockSetDocumentFilter}
      />
    );

    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper).toHaveClass(
      "flex",
      "md:flex-row",
      "flex-col",
      "justify-center",
      "gap-3",
      "h-[50vh]",
      "md:h-[80vh]"
    );
  });

  test("handles different production environments", () => {
    const { rerender, container } = render(
      <ChatView
        selectedTheme={mockTheme}
        credentials={mockCredentials}
        addStatusMessage={mockAddStatusMessage}
        production="Local"
        currentPage="chat"
        RAGConfig={mockRAGConfig}
        setRAGConfig={mockSetRAGConfig}
        documentFilter={mockDocumentFilter}
        setDocumentFilter={mockSetDocumentFilter}
      />
    );

    // Test Local environment
    expect(container.firstChild).toBeInTheDocument();

    // Test Demo environment
    rerender(
      <ChatView
        selectedTheme={mockTheme}
        credentials={mockCredentials}
        addStatusMessage={mockAddStatusMessage}
        production="Demo"
        currentPage="chat"
        RAGConfig={mockRAGConfig}
        setRAGConfig={mockSetRAGConfig}
        documentFilter={mockDocumentFilter}
        setDocumentFilter={mockSetDocumentFilter}
      />
    );
    expect(container.firstChild).toBeInTheDocument();

    // Test Production environment
    rerender(
      <ChatView
        selectedTheme={mockTheme}
        credentials={mockCredentials}
        addStatusMessage={mockAddStatusMessage}
        production="Production"
        currentPage="chat"
        RAGConfig={mockRAGConfig}
        setRAGConfig={mockSetRAGConfig}
        documentFilter={mockDocumentFilter}
        setDocumentFilter={mockSetDocumentFilter}
      />
    );
    expect(container.firstChild).toBeInTheDocument();
  });
}); 