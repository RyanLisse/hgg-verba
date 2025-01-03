import { JSDOM } from "jsdom";
import { configure } from "@testing-library/react";

// Set up DOM environment
const dom = new JSDOM("<!DOCTYPE html><html><body></body></html>", {
  url: "http://localhost",
  pretendToBeVisual: true,
  runScripts: "dangerously",
});

// Set up global DOM environment
const { window } = dom;
const { document } = window;

// Set up global variables
(global as any).window = window;
(global as any).document = document;
(global as any).navigator = window.navigator;

// Add all the window properties to the global scope
Object.keys(window).forEach((property) => {
  if (typeof (global as any)[property] === "undefined") {
    (global as any)[property] = (window as any)[property];
  }
});

// Configure testing library
configure({
  testIdAttribute: "data-testid",
});

// Mock window properties
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => {},
  }),
});

Object.defineProperty(window, "ResizeObserver", {
  writable: true,
  value: class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  },
});

// Mock canvas for Three.js
class MockCanvas {
  getContext() { return null; }
  addEventListener() {}
  removeEventListener() {}
}
(global as any).HTMLCanvasElement = MockCanvas;

// Mock requestAnimationFrame for Three.js
(global as any).requestAnimationFrame = (callback: FrameRequestCallback) => setTimeout(callback, 0);
(global as any).cancelAnimationFrame = (id: number) => clearTimeout(id);

// Mock modules
const mockModule = (id: string, exports: any): NodeModule => ({
  id,
  path: id,
  exports,
  filename: id,
  loaded: true,
  children: [],
  paths: [],
  require: require,
  parent: null,
  isPreloading: false,
});

// Mock Next.js modules
const { Plus_Jakarta_Sans, Inter, Open_Sans, PT_Mono } = require("./next/font/google/google.ts");

require.cache[require.resolve("next/font/google")] = mockModule("next/font/google", {
  Plus_Jakarta_Sans,
  Inter,
  Open_Sans,
  PT_Mono,
});

require.cache[require.resolve("next/router")] = mockModule("next/router", {
  useRouter: () => ({
    route: "/",
    pathname: "",
    query: "",
    asPath: "",
    push: () => {},
    events: {
      on: () => {},
      off: () => {},
    },
    beforePopState: () => {},
    prefetch: () => {},
  }),
});

require.cache[require.resolve("next/navigation")] = mockModule("next/navigation", {
  useRouter: () => ({
    push: () => {},
    replace: () => {},
    prefetch: () => {},
  }),
  useSearchParams: () => ({
    get: () => {},
  }),
  usePathname: () => "",
});
