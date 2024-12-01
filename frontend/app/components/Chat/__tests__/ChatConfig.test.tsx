import { describe, expect, test, vi } from "bun:test";
import { render, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ChatConfig from "../ChatConfig";
import { RAGConfig, Credentials } from "@/app/types";

describe("ChatConfig", () => {
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
            model: {
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
            model: {
              value: "gpt-3.5-turbo",
              type: "string",
              values: ["gpt-3.5-turbo", "gpt-4"]
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

  const mockSetRAGConfig = vi.fn();
  const mockOnSave = vi.fn();
  const mockOnReset = vi.fn();
  const mockAddStatusMessage = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  test("renders nothing when RAGConfig is null", () => {
    const { container } = render(
      <ChatConfig
        RAGConfig={null}
        setRAGConfig={mockSetRAGConfig}
        onSave={mockOnSave}
        onReset={mockOnReset}
        addStatusMessage={mockAddStatusMessage}
        credentials={mockCredentials}
        production="Local"
      />
    );

    expect(container.firstChild).toBeEmptyDOMElement();
  });

  test("renders save and reset buttons when RAGConfig is provided", () => {
    const { container } = render(
      <ChatConfig
        RAGConfig={mockRAGConfig}
        setRAGConfig={mockSetRAGConfig}
        onSave={mockOnSave}
        onReset={mockOnReset}
        addStatusMessage={mockAddStatusMessage}
        credentials={mockCredentials}
        production="Local"
      />
    );

    const saveButton = within(container).getByTitle("Save Config");
    const resetButton = within(container).getByTitle("Reset");
    expect(saveButton).toBeInTheDocument();
    expect(resetButton).toBeInTheDocument();
  });

  test("disables buttons in Demo mode", () => {
    const { container } = render(
      <ChatConfig
        RAGConfig={mockRAGConfig}
        setRAGConfig={mockSetRAGConfig}
        onSave={mockOnSave}
        onReset={mockOnReset}
        addStatusMessage={mockAddStatusMessage}
        credentials={mockCredentials}
        production="Demo"
      />
    );

    const saveButton = within(container).getByTitle("Save Config");
    const resetButton = within(container).getByTitle("Reset");
    expect(saveButton).toBeDisabled();
    expect(resetButton).toBeDisabled();
  });

  test("renders component views for each RAG component", () => {
    const { container } = render(
      <ChatConfig
        RAGConfig={mockRAGConfig}
        setRAGConfig={mockSetRAGConfig}
        onSave={mockOnSave}
        onReset={mockOnReset}
        addStatusMessage={mockAddStatusMessage}
        credentials={mockCredentials}
        production="Local"
      />
    );

    const componentViews = container.querySelectorAll(".flex.flex-col.justify-start.gap-3.rounded-2xl.w-full.p-6");
    expect(componentViews.length).toBe(1);
  });

  test("calls onSave when save button is clicked", async () => {
    const { container } = render(
      <ChatConfig
        RAGConfig={mockRAGConfig}
        setRAGConfig={mockSetRAGConfig}
        onSave={mockOnSave}
        onReset={mockOnReset}
        addStatusMessage={mockAddStatusMessage}
        credentials={mockCredentials}
        production="Local"
      />
    );

    const saveButton = within(container).getByTitle("Save Config");
    await userEvent.click(saveButton);
    expect(mockOnSave).toHaveBeenCalledTimes(1);
  });

  test("calls onReset when reset button is clicked", async () => {
    const { container } = render(
      <ChatConfig
        RAGConfig={mockRAGConfig}
        setRAGConfig={mockSetRAGConfig}
        onSave={mockOnSave}
        onReset={mockOnReset}
        addStatusMessage={mockAddStatusMessage}
        credentials={mockCredentials}
        production="Local"
      />
    );

    const resetButton = within(container).getByTitle("Reset");
    await userEvent.click(resetButton);
    expect(mockOnReset).toHaveBeenCalledTimes(1);
  });

  test("applies correct styling classes", () => {
    const { container } = render(
      <ChatConfig
        RAGConfig={mockRAGConfig}
        setRAGConfig={mockSetRAGConfig}
        onSave={mockOnSave}
        onReset={mockOnReset}
        addStatusMessage={mockAddStatusMessage}
        credentials={mockCredentials}
        production="Local"
      />
    );

    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper).toHaveClass("flex", "flex-col", "justify-start", "rounded-2xl", "w-full", "p-4");

    const buttonContainer = container.querySelector(".flex.justify-end.w-full.gap-2.p-4.bg-bg-alt-verba.rounded-lg");
    expect(buttonContainer).toBeInTheDocument();
  });
}); 