import { describe, expect, test } from "bun:test";
import { render, within } from "@testing-library/react";
import StatusLabel from "../StatusLabel";

describe("StatusLabel", () => {
  test("renders with true status correctly", () => {
    const { container } = render(
      <StatusLabel
        status={true}
        true_text="Connected"
        false_text="Disconnected"
      />
    );

    const label = within(container).getByText("Connected");
    expect(label).toBeInTheDocument();
    expect(label.className).toContain("text-text-verba");
    expect(container.firstChild).toHaveClass("bg-secondary-verba");
  });

  test("renders with false status correctly", () => {
    const { container } = render(
      <StatusLabel
        status={false}
        true_text="Connected"
        false_text="Disconnected"
      />
    );

    const label = within(container).getByText("Disconnected");
    expect(label).toBeInTheDocument();
    expect(label.className).toContain("text-text-alt-verba");
    expect(container.firstChild).toHaveClass("bg-bg-alt-verba");
  });

  test("updates text when status changes", () => {
    const { container, rerender } = render(
      <StatusLabel
        status={true}
        true_text="Online"
        false_text="Offline"
      />
    );

    expect(within(container).getByText("Online")).toBeInTheDocument();

    rerender(
      <StatusLabel
        status={false}
        true_text="Online"
        false_text="Offline"
      />
    );

    expect(within(container).getByText("Offline")).toBeInTheDocument();
  });

  test("applies correct styling classes", () => {
    const { container } = render(
      <StatusLabel
        status={true}
        true_text="Success"
        false_text="Error"
      />
    );

    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper).toHaveClass("p-2", "rounded-lg", "text-text-verba", "text-sm");
    
    const textElement = wrapper.firstChild as HTMLElement;
    expect(textElement).toHaveClass("text-xs", "text-text-verba");
  });
}); 