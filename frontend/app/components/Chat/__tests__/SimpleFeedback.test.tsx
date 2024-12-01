import { describe, expect, test, vi, beforeEach, afterEach } from "bun:test";
import { render, fireEvent, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import SimpleFeedback from "../SimpleFeedback";

describe("SimpleFeedback", () => {
  let mockOnSubmit;
  let container;

  beforeEach(() => {
    mockOnSubmit = vi.fn();
  });

  afterEach(() => {
    if (container) {
      document.body.removeChild(container);
    }
  });

  test("renders feedback button disabled when no runId", () => {
    const { container: renderContainer } = render(<SimpleFeedback runId="" onSubmit={mockOnSubmit} />);
    container = renderContainer;
    const feedbackButton = within(container).getByRole('button', { name: /feedback/i });
    expect(feedbackButton).toBeDisabled();
  });

  test("renders feedback button enabled with runId", () => {
    const { container: renderContainer } = render(<SimpleFeedback runId="test-123" onSubmit={mockOnSubmit} />);
    container = renderContainer;
    const feedbackButton = within(container).getByRole('button', { name: /feedback/i });
    expect(feedbackButton).toBeEnabled();
  });

  test("opens modal when feedback button is clicked", async () => {
    const { container: renderContainer } = render(<SimpleFeedback runId="test-123" onSubmit={mockOnSubmit} />);
    container = renderContainer;
    const feedbackButton = within(container).getByRole('button', { name: /feedback/i });
    await userEvent.click(feedbackButton);

    const modal = within(container).getByRole('dialog');
    expect(modal).toBeInTheDocument();
  });

  test("shows thumbs up/down buttons in modal", async () => {
    const { container: renderContainer } = render(<SimpleFeedback runId="test-123" onSubmit={mockOnSubmit} />);
    container = renderContainer;
    const feedbackButton = within(container).getByRole('button', { name: /feedback/i });
    await userEvent.click(feedbackButton);

    const thumbsUpButton = within(container).getByRole('button', { name: /yes/i });
    const thumbsDownButton = within(container).getByRole('button', { name: /no/i });

    expect(thumbsUpButton).toBeInTheDocument();
    expect(thumbsDownButton).toBeInTheDocument();
  });

  test("submits positive feedback when clicking thumbs up", async () => {
    const { container: renderContainer } = render(<SimpleFeedback runId="test-123" onSubmit={mockOnSubmit} />);
    container = renderContainer;
    const feedbackButton = within(container).getByRole('button', { name: /feedback/i });
    await userEvent.click(feedbackButton);

    const thumbsUpButton = within(container).getByRole('button', { name: /yes/i });
    await userEvent.click(thumbsUpButton);

    expect(mockOnSubmit).toHaveBeenCalledWith("test-123", "positive", "");
  });

  test("shows textarea when clicking thumbs down", async () => {
    const { container: renderContainer } = render(<SimpleFeedback runId="test-123" onSubmit={mockOnSubmit} />);
    container = renderContainer;
    const feedbackButton = within(container).getByRole('button', { name: /feedback/i });
    await userEvent.click(feedbackButton);

    const thumbsDownButton = within(container).getByRole('button', { name: /no/i });
    await userEvent.click(thumbsDownButton);

    const textarea = within(container).getByRole('textbox');
    expect(textarea).toBeInTheDocument();
  });

  test("submits negative feedback with comments", async () => {
    const { container: renderContainer } = render(<SimpleFeedback runId="test-123" onSubmit={mockOnSubmit} />);
    container = renderContainer;
    const feedbackButton = within(container).getByRole('button', { name: /feedback/i });
    await userEvent.click(feedbackButton);

    const thumbsDownButton = within(container).getByRole('button', { name: /no/i });
    await userEvent.click(thumbsDownButton);

    const textarea = within(container).getByRole('textbox');
    await userEvent.type(textarea, "Test feedback comment");

    const submitButton = within(container).getByRole('button', { name: /submit/i });
    await userEvent.click(submitButton);

    expect(mockOnSubmit).toHaveBeenCalledWith("test-123", "negative", "Test feedback comment");
  });

  test("closes modal when clicking escape", async () => {
    const { container: renderContainer } = render(<SimpleFeedback runId="test-123" onSubmit={mockOnSubmit} />);
    container = renderContainer;
    const feedbackButton = within(container).getByRole('button', { name: /feedback/i });
    await userEvent.click(feedbackButton);

    const modal = within(container).getByRole('dialog');
    expect(modal).toBeInTheDocument();

    fireEvent.keyDown(document, { key: "Escape", code: "Escape", keyCode: 27 });

    expect(within(container).queryByRole('dialog')).not.toBeInTheDocument();
  });

  test("modal remains open when submitting invalid negative feedback", async () => {
    const { container: renderContainer } = render(<SimpleFeedback runId="test-123" onSubmit={mockOnSubmit} />);
    container = renderContainer;
    const feedbackButton = within(container).getByRole('button', { name: /feedback/i });
    await userEvent.click(feedbackButton);

    const thumbsDownButton = within(container).getByRole('button', { name: /no/i });
    await userEvent.click(thumbsDownButton);

    const submitButton = within(container).getByRole('button', { name: /submit/i });
    await userEvent.click(submitButton);

    const modal = within(container).getByRole('dialog');
    expect(modal).toBeInTheDocument();
    expect(mockOnSubmit).not.toHaveBeenCalled();
  });
});
