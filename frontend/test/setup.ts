import { JSDOM } from "jsdom";
import { expect, mock } from "bun:test";

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
  Plus_Jakarta_Sans: () => ({
    className: "mocked-font",
    style: { fontFamily: "Plus_Jakarta_Sans" },
  }),
  Open_Sans: () => ({
    className: "mocked-font",
    style: { fontFamily: "Open_Sans" },
  }),
  PT_Mono: () => ({
    className: "mocked-font",
    style: { fontFamily: "PT_Mono" },
  }),
  Inter: () => ({
    className: "mocked-font",
    style: { fontFamily: "Inter" },
  }),
}));

// Add test matchers
expect.extend({
  toBeInTheDocument(received: any) {
    return {
      pass: received !== null && received !== undefined,
      message: () => "element should be in the document",
    };
  },
  toBeDisabled(received: any) {
    return {
      pass: received?.disabled === true,
      message: () => "element should be disabled",
    };
  },
  toHaveClass(received: any, className: string) {
    return {
      pass: received?.className?.includes(className),
      message: () => `element should have class ${className}`,
    };
  },
});

// Add test matchers types
declare global {
  namespace jest {
    interface Matchers<R, T = {}> {
      toBeInTheDocument(): R;
      toBeDisabled(): R;
      toHaveClass(className: string): R;
      toHaveAttribute(attr: string, value?: string): R;
      toHaveTextContent(text: string): R;
      toHaveLength(length: number): R;
      toHaveBeenCalledWith(...args: any[]): R;
      toHaveBeenCalledTimes(times: number): R;
      toHaveBeenLastCalledWith(...args: any[]): R;
    }
  }
}

// Add DOM element types
declare global {
  interface Window {
    HTMLElement: typeof HTMLElement;
    HTMLInputElement: typeof HTMLInputElement;
  }
}
