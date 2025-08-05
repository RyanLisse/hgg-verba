import { beforeEach, describe, expect, mock, test } from "bun:test";
import { fireEvent, render, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import SimpleFeedback from "../SimpleFeedback";

describe("SimpleFeedback", () => {
  const mockRunId = "test-run-id";
  let mockOnSubmit: any;

  beforeEach(() => {
    mockOnSubmit = mock(() => {});
  });

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

    fireEvent.click(
      within(container).getByRole("button", { name: /feedback/i })
    );
    fireEvent.click(within(container).getByRole("button", { name: /yes/i }));

    expect(mockOnSubmit.mock.calls.length).toBe(1);
    expect(mockOnSubmit.mock.calls[0]).toEqual([mockRunId, "positive", ""]);
  });

  test("shows textarea for negative feedback", () => {
    const { container } = render(
      <SimpleFeedback runId={mockRunId} onSubmit={mockOnSubmit} />
    );

    fireEvent.click(
      within(container).getByRole("button", { name: /feedback/i })
    );
    fireEvent.click(within(container).getByRole("button", { name: /no/i }));

    const textarea = container.querySelector("textarea");
    expect(textarea).toBeInTheDocument();
  });

  test("handles negative feedback submission", async () => {
    const user = userEvent.setup();
    const { container } = render(
      <SimpleFeedback runId={mockRunId} onSubmit={mockOnSubmit} />
    );

    fireEvent.click(
      within(container).getByRole("button", { name: /feedback/i })
    );
    fireEvent.click(within(container).getByRole("button", { name: /no/i }));

    const textarea = container.querySelector("textarea") as HTMLTextAreaElement;
    await user.type(textarea, "Test feedback");
    await user.click(
      within(container).getByRole("button", { name: /submit feedback/i })
    );

    expect(mockOnSubmit.mock.calls.length).toBe(1);
    expect(mockOnSubmit.mock.calls[0]).toEqual([
      mockRunId,
      "negative",
      "Test feedback",
    ]);
  });
});
