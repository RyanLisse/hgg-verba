import { describe, expect, test } from "bun:test";
import type { Chunk } from "@/app/types/chat";
import { render, within } from "@testing-library/react";
import ContentView from "../ContentView";

describe("ContentView", () => {
  const mockChunks: Chunk[] = [
    {
      source: "document1.pdf",
      score: 0.9,
      content: "First chunk content",
      page: 1,
    },
    {
      source: "document2.pdf",
      score: 0.8,
      content: "Second chunk content",
      page: 2,
    },
  ];

  test("renders title correctly", () => {
    const { container } = render(<ContentView chunks={mockChunks} />);

    const title = within(container).getByText("Retrieved Chunks:");
    expect(title).toBeInTheDocument();
    expect(title.tagName).toBe("H3");
    expect(title).toHaveClass("text-lg", "font-semibold", "mb-2");
  });

  test("renders all chunks", () => {
    const { container } = render(<ContentView chunks={mockChunks} />);

    const firstChunkContent = within(container).getByText(
      "First chunk content"
    );
    const secondChunkContent = within(container).getByText(
      "Second chunk content"
    );
    expect(firstChunkContent).toBeInTheDocument();
    expect(secondChunkContent).toBeInTheDocument();
  });

  test("renders chunk sources and scores", () => {
    const { container } = render(<ContentView chunks={mockChunks} />);

    const firstChunkInfo = within(container).getByText(
      "Source: document1.pdf (Score: 0.9000)"
    );
    const secondChunkInfo = within(container).getByText(
      "Source: document2.pdf (Score: 0.8000)"
    );
    expect(firstChunkInfo).toBeInTheDocument();
    expect(secondChunkInfo).toBeInTheDocument();
  });

  test("handles empty chunks array", () => {
    const { container } = render(<ContentView chunks={[]} />);

    const title = within(container).getByText("Retrieved Chunks:");
    expect(title).toBeInTheDocument();
    expect(container.querySelectorAll(".mb-4")).toHaveLength(0);
  });

  test("applies correct wrapper styling", () => {
    const { container } = render(<ContentView chunks={mockChunks} />);

    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper).toHaveClass("mt-4");
  });

  test("renders chunks in correct order", () => {
    const { container } = render(<ContentView chunks={mockChunks} />);

    const chunkElements = container.querySelectorAll(".mb-4");
    expect(chunkElements).toHaveLength(2);

    const firstChunkText = within(chunkElements[0]).getByText(
      "First chunk content"
    );
    const secondChunkText = within(chunkElements[1]).getByText(
      "Second chunk content"
    );
    expect(firstChunkText).toBeInTheDocument();
    expect(secondChunkText).toBeInTheDocument();
  });
});
