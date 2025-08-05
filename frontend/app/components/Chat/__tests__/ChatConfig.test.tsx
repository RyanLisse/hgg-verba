import { describe, expect, mock, test } from "bun:test";
import type { RAGConfig } from "@/app/types";
import { fireEvent, render, within } from "@testing-library/react";
import ChatConfig from "../ChatConfig";

describe("ChatConfig", () => {
  const mockConfig: RAGConfig = {
    Embedder: {
      selected: "OpenAIEmbeddings",
      components: {
        OpenAIEmbeddings: {
          config: {
            Model: {
              value: "text-embedding-3-large",
              type: "string",
              values: ["text-embedding-3-large"],
            },
          },
        },
      },
    },
    Generator: {
      selected: "ChatOpenAI",
      components: {
        ChatOpenAI: {
          config: {
            Model: {
              value: "gpt-4",
              type: "string",
              values: ["gpt-4", "gpt-3.5-turbo"],
            },
          },
        },
      },
    },
    Retriever: {
      selected: "MultiQueryRetriever",
      components: {
        MultiQueryRetriever: {
          config: {
            search_type: {
              value: "similarity",
              type: "string",
              values: ["similarity", "mmr"],
            },
          },
        },
      },
    },
  };

  const mockCredentials = {
    url: "test-url",
    username: "test-user",
    password: "test-pass",
  };

  const defaultProps = {
    RAGConfig: mockConfig,
    setRAGConfig: mock(() => {}),
    onSave: mock(() => {}),
    onReset: mock(() => {}),
    addStatusMessage: mock((message: string, type: string) => {}),
    credentials: mockCredentials,
    production: "Local" as const,
  };

  test("renders config form correctly", () => {
    const { container } = render(<ChatConfig {...defaultProps} />);

    // Check for main container
    const mainContainer = container.querySelector(
      ".flex.flex-col.justify-start.rounded-2xl.w-full"
    );
    expect(mainContainer).toBeInTheDocument();

    // Check for save and reset buttons
    const saveButton = within(container).getByText("Save Config");
    const resetButton = within(container).getByText("Reset");
    expect(saveButton).toBeInTheDocument();
    expect(resetButton).toBeInTheDocument();

    // Check for component sections
    expect(within(container).getByText("Embedder")).toBeInTheDocument();
    expect(within(container).getByText("Generator")).toBeInTheDocument();
    expect(within(container).getByText("Retriever")).toBeInTheDocument();
  });

  test("buttons are enabled in Local mode", () => {
    const { container } = render(<ChatConfig {...defaultProps} />);

    const saveButton = within(container)
      .getByText("Save Config")
      .closest("button");
    const resetButton = within(container).getByText("Reset").closest("button");
    expect(saveButton?.getAttribute("disabled")).toBeFalsy();
    expect(resetButton?.getAttribute("disabled")).toBeFalsy();
  });

  test("buttons are disabled in Demo mode", () => {
    const { container } = render(
      <ChatConfig {...defaultProps} production="Demo" />
    );

    const saveButton = within(container)
      .getByText("Save Config")
      .closest("button");
    const resetButton = within(container).getByText("Reset").closest("button");
    expect(saveButton?.getAttribute("disabled")).toBe("");
    expect(resetButton?.getAttribute("disabled")).toBe("");
  });

  test("calls onSave when save button is clicked", () => {
    const mockOnSave = mock(() => {});
    const { container } = render(
      <ChatConfig {...defaultProps} onSave={mockOnSave} />
    );

    const saveButton = within(container).getByText("Save Config");
    fireEvent.click(saveButton);
    expect(mockOnSave).toHaveBeenCalledTimes(1);
  });

  test("calls onReset when reset button is clicked", () => {
    const mockOnReset = mock(() => {});
    const { container } = render(
      <ChatConfig {...defaultProps} onReset={mockOnReset} />
    );

    const resetButton = within(container).getByText("Reset");
    fireEvent.click(resetButton);
    expect(mockOnReset).toHaveBeenCalledTimes(1);
  });

  test("renders empty div when RAGConfig is null", () => {
    const { container } = render(
      <ChatConfig {...defaultProps} RAGConfig={null} />
    );

    expect(container.firstChild?.textContent).toBe("");
  });

  test("updates config when component is selected", () => {
    const mockSetRAGConfig = mock(() => {});
    const { container } = render(
      <ChatConfig {...defaultProps} setRAGConfig={mockSetRAGConfig} />
    );

    // Find and click the Embedder component
    const embedderSection = within(container)
      .getByText("Embedder")
      .closest(".flex.flex-col");
    expect(embedderSection).toBeInTheDocument();

    // Verify that OpenAIEmbeddings is selected
    expect(within(container).getByText("OpenAIEmbeddings")).toBeInTheDocument();
  });

  test("shows component configuration options", () => {
    const { container } = render(<ChatConfig {...defaultProps} />);

    // Check Generator section
    const generatorSection = within(container)
      .getByText("Generator")
      .closest(".flex.flex-col");
    expect(generatorSection).toBeInTheDocument();

    // Verify that ChatOpenAI is selected
    expect(within(container).getByText("ChatOpenAI")).toBeInTheDocument();
  });

  test("shows retriever configuration options", () => {
    const { container } = render(<ChatConfig {...defaultProps} />);

    // Check Retriever section
    const retrieverSection = within(container)
      .getByText("Retriever")
      .closest(".flex.flex-col");
    expect(retrieverSection).toBeInTheDocument();

    // Verify that MultiQueryRetriever is selected
    expect(
      within(container).getByText("MultiQueryRetriever")
    ).toBeInTheDocument();
  });
});
