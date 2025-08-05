import { describe, expect, test } from "bun:test";
import type { Chunk } from "@/app/types/chat";
import { render, within } from "@testing-library/react";
import ChunkView from "../ChunkView";

describe("ChunkView", () => {
  const mockChunk: Chunk = {
    source: "test-document.pdf",
    score: 0.8765,
    content: "This is a test chunk content\nwith multiple lines",
    page: 1,
  };

  test("renders chunk content correctly", () => {
    const { container } = render(<ChunkView chunk={mockChunk} />);

    const content = container.querySelector(".whitespace-pre-wrap");
    expect(content).toBeInTheDocument();
    expect(content?.textContent).toBe(mockChunk.content);
  });

  test("displays source and score information", () => {
    const { container } = render(<ChunkView chunk={mockChunk} />);

    const sourceInfo = within(container).getByText(
      "Source: test-document.pdf (Score: 0.8765)"
    );
    expect(sourceInfo).toBeInTheDocument();
    expect(sourceInfo.className).toContain("text-sm");
    expect(sourceInfo.className).toContain("text-gray-600");
  });

  test("applies correct styling classes", () => {
    const { container } = render(<ChunkView chunk={mockChunk} />);

    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper).toHaveClass("mb-4", "p-4", "bg-gray-100", "rounded-lg");
  });

  test("handles chunk with empty content", () => {
    const emptyChunk: Chunk = {
      ...mockChunk,
      content: "",
    };

    const { container } = render(<ChunkView chunk={emptyChunk} />);
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper).toBeInTheDocument();
    expect(
      within(wrapper).getByText("Source: test-document.pdf (Score: 0.8765)")
    ).toBeInTheDocument();
  });

  test("formats score to 4 decimal places", () => {
    const preciseChunk: Chunk = {
      ...mockChunk,
      score: 0.87654321,
    };

    const { container } = render(<ChunkView chunk={preciseChunk} />);
    const sourceInfo = within(container).getByText(
      "Source: test-document.pdf (Score: 0.8765)"
    );
    expect(sourceInfo).toBeInTheDocument();
  });
});
