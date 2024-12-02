import { describe, expect, test, mock } from "bun:test";
import { render, fireEvent, within } from "@testing-library/react";
import SimpleFeedback from "../SimpleFeedback";

describe("SimpleFeedback", () => {
  const mockRunId = "test-run-id";
  const mockOnSubmit = mock((runId: string, feedbackType: string, additionalFeedback: string) => {});

  test("renders feedback button correctly", () => {
    const { container } = render(
      <SimpleFeedback runId={mockRunId} onSubmit={mockOnSubmit} />
    );

    const button = within(container).getByRole("button", { name: /feedback/i });
    expect(button).toBeInTheDocument();
    expect(button).not.toBeDisabled();
  });

  test("opens feedback dialog when button is clicked", () => {
    const { container } = render(
      <SimpleFeedback runId={mockRunId} onSubmit={mockOnSubmit} />
    );

    const button = within(container).getByRole("button", { name: /feedback/i });
    fireEvent.click(button);

    const dialog = within(container).getByRole("dialog");
    expect(dialog).toBeInTheDocument();
    expect(within(dialog).getByText("Was this helpful?")).toBeInTheDocument();
  });

  test("handles positive feedback submission", () => {
    const { container } = render(
      <SimpleFeedback runId={mockRunId} onSubmit={mockOnSubmit} />
    );

    fireEvent.click(within(container).getByRole("button", { name: /feedback/i }));
    fireEvent.click(within(container).getByRole("button", { name: /yes/i }));

    expect(mockOnSubmit).toHaveBeenCalledWith(mockRunId, "positive", "");
  });

  test("shows textarea for negative feedback", () => {
    const { container } = render(
      <SimpleFeedback runId={mockRunId} onSubmit={mockOnSubmit} />
    );

    fireEvent.click(within(container).getByRole("button", { name: /feedback/i }));
    fireEvent.click(within(container).getByRole("button", { name: /no/i }));

    const textarea = container.querySelector("textarea");
    expect(textarea).toBeInTheDocument();
  });

  test("handles negative feedback submission", () => {
    mockOnSubmit.mockClear();
    const { container } = render(
      <SimpleFeedback runId={mockRunId} onSubmit={mockOnSubmit} />
    );

    fireEvent.click(within(container).getByRole("button", { name: /feedback/i }));
    fireEvent.click(within(container).getByRole("button", { name: /no/i }));

    const textarea = container.querySelector("textarea") as HTMLTextAreaElement;
    fireEvent.change(textarea, { target: { value: "Test feedback" } });
    fireEvent.click(within(container).getByRole("button", { name: /submit feedback/i }));

    expect(mockOnSubmit).toHaveBeenCalledTimes(1);
    expect(mockOnSubmit).toHaveBeenLastCalledWith(mockRunId, "negative", "Test feedback");
  });
}); 