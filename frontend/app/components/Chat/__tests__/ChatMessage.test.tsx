import { describe, expect, test, vi, beforeEach } from "bun:test";
import { render, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ChatMessage from "../ChatMessage";
import { Theme, Message, ChunkScore } from "@/app/types";

describe("ChatMessage", () => {
  const mockTheme: Theme = {
    theme: "light",
    color: "#000000"
  };

  const mockSetSelectedDocument = vi.fn();
  const mockSetSelectedDocumentScore = vi.fn();
  const mockSetSelectedChunkScore = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  test("renders user message correctly", () => {
    const message: Message = {
      type: "user",
      content: "Hello, world!",
      cached: false
    };

    const { container } = render(
      <ChatMessage
        message={message}
        message_index={0}
        selectedTheme={mockTheme}
        selectedDocument={null}
        setSelectedDocument={mockSetSelectedDocument}
        setSelectedDocumentScore={mockSetSelectedDocumentScore}
        setSelectedChunkScore={mockSetSelectedChunkScore}
      />
    );

    const messageContent = within(container).getByText("Hello, world!");
    expect(messageContent).toBeInTheDocument();
    expect(container.querySelector(".justify-end")).toBeInTheDocument();
  });

  test("renders system message with markdown correctly", () => {
    const message: Message = {
      type: "system",
      content: "**Bold text** and `code`",
      cached: false
    };

    const { container } = render(
      <ChatMessage
        message={message}
        message_index={0}
        selectedTheme={mockTheme}
        selectedDocument={null}
        setSelectedDocument={mockSetSelectedDocument}
        setSelectedDocumentScore={mockSetSelectedDocumentScore}
        setSelectedChunkScore={mockSetSelectedChunkScore}
      />
    );

    const boldText = within(container).getByText("Bold text");
    expect(boldText.tagName).toBe("STRONG");
    const codeElement = container.querySelector("code");
    expect(codeElement).toBeInTheDocument();
  });

  test("renders error message with icon", () => {
    const message: Message = {
      type: "error",
      content: "Error occurred",
      cached: false
    };

    const { container } = render(
      <ChatMessage
        message={message}
        message_index={0}
        selectedTheme={mockTheme}
        selectedDocument={null}
        setSelectedDocument={mockSetSelectedDocument}
        setSelectedDocumentScore={mockSetSelectedDocumentScore}
        setSelectedChunkScore={mockSetSelectedChunkScore}
      />
    );

    const errorIcon = container.querySelector("svg");
    const errorText = within(container).getByText("Error occurred");
    expect(errorIcon).toBeInTheDocument();
    expect(errorText).toBeInTheDocument();
  });

  test("shows database icon for cached messages", () => {
    const message: Message = {
      type: "user",
      content: "Cached message",
      cached: true
    };

    const { container } = render(
      <ChatMessage
        message={message}
        message_index={0}
        selectedTheme={mockTheme}
        selectedDocument={null}
        setSelectedDocument={mockSetSelectedDocument}
        setSelectedDocumentScore={mockSetSelectedDocumentScore}
        setSelectedChunkScore={mockSetSelectedChunkScore}
      />
    );

    const databaseIcon = container.querySelector(".fa-database");
    expect(databaseIcon).toBeInTheDocument();
  });

  test("renders retrieval message with document buttons", async () => {
    const chunks: ChunkScore[] = [{ score: 0.8, content: "chunk1", page: 1 }];
    const message: Message = {
      type: "retrieval",
      content: [{
        title: "Document 1",
        uuid: "doc1",
        score: 0.9,
        chunks: chunks
      }],
      cached: false
    };

    const { container } = render(
      <ChatMessage
        message={message}
        message_index={0}
        selectedTheme={mockTheme}
        selectedDocument={null}
        setSelectedDocument={mockSetSelectedDocument}
        setSelectedDocumentScore={mockSetSelectedDocumentScore}
        setSelectedChunkScore={mockSetSelectedChunkScore}
      />
    );

    const documentButton = within(container).getByText("Document 1");
    await userEvent.click(documentButton);

    expect(mockSetSelectedDocument).toHaveBeenCalledWith("doc1");
    expect(mockSetSelectedDocumentScore).toHaveBeenCalledWith("doc10.9" + chunks.length);
    expect(mockSetSelectedChunkScore).toHaveBeenCalledWith(chunks);
  });

  test("opens context modal when clicking attach button", async () => {
    const message: Message = {
      type: "retrieval",
      content: [],
      cached: false,
      context: "Context information"
    };

    const { container } = render(
      <ChatMessage
        message={message}
        message_index={0}
        selectedTheme={mockTheme}
        selectedDocument={null}
        setSelectedDocument={mockSetSelectedDocument}
        setSelectedDocumentScore={mockSetSelectedDocumentScore}
        setSelectedChunkScore={mockSetSelectedChunkScore}
      />
    );

    const attachButton = container.querySelector(".btn-square");
    expect(attachButton).toBeInTheDocument();
    await userEvent.click(attachButton!);

    const modal = document.querySelector("dialog");
    expect(modal).toBeInTheDocument();
    expect(within(modal!).getByText("Context information")).toBeInTheDocument();
  });
}); 