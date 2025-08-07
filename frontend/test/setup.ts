import { expect, mock } from "bun:test";
import { JSDOM } from "jsdom";

// Set up DOM environment first
const dom = new JSDOM("<!DOCTYPE html><html><body></body></html>");
const { window } = dom;

// Set up global variables
Object.defineProperty(global, "window", {
  value: window,
  writable: true,
});

Object.defineProperty(global, "document", {
  value: window.document,
  writable: true,
});

Object.defineProperty(global, "navigator", {
  value: window.navigator,
  writable: true,
});

// Mock Next.js font modules
mock.module("next/font/google", () => ({
  plusJakartaSans: () => ({
    className: "mocked-font",
    style: { fontFamily: "Plus_Jakarta_Sans" },
  }),
  openSans: () => ({
    className: "mocked-font",
    style: { fontFamily: "Open_Sans" },
  }),
  ptMono: () => ({
    className: "mocked-font",
    style: { fontFamily: "PT_Mono" },
  }),
  inter: () => ({
    className: "mocked-font",
    style: { fontFamily: "Inter" },
  }),
}));

// Add test matchers
expect.extend({
  toBeInTheDocument(received: unknown) {
    const element = received as Element | null | undefined;
    return {
      pass: element !== null && element !== undefined,
      message: () => "element should be in the document",
    };
  },
  toBeDisabled(received: unknown) {
    const element = received as HTMLElement | null | undefined;
    return {
      pass: (element as HTMLInputElement)?.disabled === true,
      message: () => "element should be disabled",
    };
  },
  toHaveClass(received: unknown, className: string) {
    const element = received as Element | null | undefined;
    return {
      pass: element?.className?.includes(className) === true,
      message: () => `element should have class ${className}`,
    };
  },
});

// Add test matchers types
declare global {
  namespace jest {
    interface Matchers<R> {
      toBeInTheDocument(): R;
      toBeDisabled(): R;
      toHaveClass(className: string): R;
      toHaveAttribute(attr: string, value?: string): R;
      toHaveTextContent(text: string): R;
      toHaveLength(length: number): R;
      toHaveBeenCalledWith(...args: unknown[]): R;
      toHaveBeenCalledTimes(times: number): R;
      toHaveBeenLastCalledWith(...args: unknown[]): R;
    }
  }
}

// Add DOM element types
declare global {
  interface Window {
    htmlElement: typeof HTMLElement;
    htmlInputElement: typeof HTMLInputElement;
  }
}
