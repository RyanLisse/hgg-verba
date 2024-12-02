import { describe, expect, test } from "bun:test";
import { render, within } from "@testing-library/react";
import ChatMessage from "../ChatMessage";
import { Message, Theme } from "@/app/types";

describe("ChatMessage", () => {
  const mockTheme: Theme = {
    theme: "light",
    color: "#000000"
  };

  const defaultProps = {
    message_index: 0,
    selectedTheme: mockTheme,
    selectedDocument: null,
    setSelectedDocument: () => {},
    setSelectedDocumentScore: () => {},
    setSelectedChunkScore: () => {}
  };

  test("renders user message correctly", () => {
    const message: Message = {
      role: "user",
      content: "Hello, world!",
      type: "user"
    };

    const { container } = render(
      <ChatMessage message={message} {...defaultProps} />
    );

    const messageDiv = container.querySelector(".whitespace-pre-wrap");
    expect(messageDiv).toBeInTheDocument();
    expect(messageDiv?.textContent).toBe("Hello, world!");
  });

  test("renders system message with markdown correctly", () => {
    const message: Message = {
      role: "assistant",
      content: "**Hello**, *world*!",
      type: "system"
    };

    const { container } = render(
      <ChatMessage message={message} {...defaultProps} />
    );

    const markdownContent = container.querySelector(".prose");
    expect(markdownContent).toBeInTheDocument();
    const strongElement = container.querySelector("strong");
    expect(strongElement).toBeInTheDocument();
    expect(strongElement?.textContent).toBe("Hello");
  });

  test("renders error message correctly", () => {
    const message: Message = {
      role: "assistant",
      content: "Error occurred",
      type: "error"
    };

    const { container } = render(
      <ChatMessage message={message} {...defaultProps} />
    );

    const errorDiv = container.querySelector(".text-text-verba");
    expect(errorDiv).toBeInTheDocument();
    expect(errorDiv?.textContent).toContain("Error occurred");
  });

  test("renders retrieval message correctly", () => {
    const message: Message = {
      role: "assistant",
      content: [
        {
          title: "test.pdf",
          uuid: "test-uuid",
          score: 0.8,
          chunks: [
            {
              source: "test.pdf",
              score: 0.8,
              content: "Test chunk content",
              page: 1
            }
          ]
        }
      ],
      type: "retrieval"
    };

    const { container } = render(
      <ChatMessage message={message} {...defaultProps} />
    );

    const documentTitle = container.querySelector(".truncate");
    expect(documentTitle).toBeInTheDocument();
    expect(documentTitle?.textContent).toBe("test.pdf");
  });

  test("renders context information", () => {
    const message: Message = {
      role: "assistant",
      content: [
        {
          title: "test.pdf",
          uuid: "test-uuid",
          score: 0.8,
          chunks: [
            {
              source: "test.pdf",
              score: 0.8,
              content: "Test chunk content",
              page: 1
            }
          ]
        }
      ],
      type: "retrieval",
      context: "Test context"
    };

    const { container } = render(
      <ChatMessage message={message} {...defaultProps} />
    );

    const contextButton = container.querySelector(".btn-square");
    expect(contextButton).toBeInTheDocument();
  });
}); 