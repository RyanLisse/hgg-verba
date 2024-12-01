import { describe, expect, test } from "bun:test";
import { render } from "@testing-library/react";
import ChatMessage from "../ChatMessage";
import { Theme } from "@/app/types";

describe("ChatMessage", () => {
  const mockTheme: Theme = {
    theme: "light",
    color: "#000000"
  };

  test("renders user message correctly", () => {
    const { container } = render(
      <ChatMessage
        message={{
          type: "user",
          content: "Test user message",
          role: "user"
        }}
        message_index={0}
        selectedTheme={mockTheme}
        selectedDocument={null}
        setSelectedDocument={() => {}}
        setSelectedDocumentScore={() => {}}
        setSelectedChunkScore={() => {}}
      />
    );

    expect(container.textContent).toContain("Test user message");
  });

  test("renders system message with markdown correctly", () => {
    const { container } = render(
      <ChatMessage
        message={{
          type: "system",
          content: "**Test** system message",
          role: "system"
        }}
        message_index={0}
        selectedTheme={mockTheme}
        selectedDocument={null}
        setSelectedDocument={() => {}}
        setSelectedDocumentScore={() => {}}
        setSelectedChunkScore={() => {}}
      />
    );

    const boldText = container.querySelector("strong");
    expect(boldText).toBeInTheDocument();
    expect(boldText?.textContent).toBe("Test");
    expect(container.textContent).toContain("system message");
  });

  test("renders error message correctly", () => {
    const { container } = render(
      <ChatMessage
        message={{
          type: "error",
          content: "Test error message",
          role: "system"
        }}
        message_index={0}
        selectedTheme={mockTheme}
        selectedDocument={null}
        setSelectedDocument={() => {}}
        setSelectedDocumentScore={() => {}}
        setSelectedChunkScore={() => {}}
      />
    );

    expect(container.textContent).toContain("Test error message");
  });

  test.skip("shows database icon for cached messages", () => {
    const { container } = render(
      <ChatMessage
        message={{
          type: "system",
          content: "Test cached message",
          role: "system",
          cached: true
        }}
        message_index={0}
        selectedTheme={mockTheme}
        selectedDocument={null}
        setSelectedDocument={() => {}}
        setSelectedDocumentScore={() => {}}
        setSelectedChunkScore={() => {}}
      />
    );

    expect(container.querySelector(".fa-database")).toBeInTheDocument();
  });

  test("renders retrieval message correctly", () => {
    const { container } = render(
      <ChatMessage
        message={{
          type: "retrieval",
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
          role: "system"
        }}
        message_index={0}
        selectedTheme={mockTheme}
        selectedDocument={null}
        setSelectedDocument={() => {}}
        setSelectedDocumentScore={() => {}}
        setSelectedChunkScore={() => {}}
      />
    );

    expect(container.textContent).toContain("test.pdf");
  });

  test("renders context information", () => {
    const { container } = render(
      <ChatMessage
        message={{
          type: "retrieval",
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
          role: "system",
          context: "Test context"
        }}
        message_index={0}
        selectedTheme={mockTheme}
        selectedDocument={null}
        setSelectedDocument={() => {}}
        setSelectedDocumentScore={() => {}}
        setSelectedChunkScore={() => {}}
      />
    );

    expect(container.textContent).toContain("test.pdf");
  });
}); 