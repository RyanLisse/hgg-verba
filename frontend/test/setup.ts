import { JSDOM } from "jsdom";
import { configure } from "@testing-library/react";
import * as matchers from "@testing-library/jest-dom/matchers";
import { expect, mock } from "bun:test";

// Set up DOM environment first
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
(global as any).HTMLElement = window.HTMLElement;
(global as any).HTMLInputElement = window.HTMLInputElement;

// Add all the window properties to the global scope
Object.keys(window).forEach((property) => {
  if (typeof (global as any)[property] === "undefined") {
    (global as any)[property] = (window as any)[property];
  }
});

// Extend HTMLElement interface
declare global {
  interface HTMLElement {
    attachEvent(event: string, handler: Function): void;
    detachEvent(event: string, handler: Function): void;
  }
}

expect.extend(matchers);

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

// Mock Next.js font modules
mock.module("next/font/google", () => ({
  Plus_Jakarta_Sans: () => ({
    className: 'mock-plus-jakarta-sans',
    style: { fontFamily: 'Plus Jakarta Sans' },
    variable: '--font-plus-jakarta-sans'
  }),
  Inter: () => ({
    className: 'mock-inter',
    style: { fontFamily: 'Inter' },
    variable: '--font-inter'
  }),
  Open_Sans: () => ({
    className: 'mock-open-sans',
    style: { fontFamily: 'Open Sans' },
    variable: '--font-open-sans'
  }),
  PT_Mono: () => ({
    className: 'mock-pt-mono',
    style: { fontFamily: 'PT Mono' },
    variable: '--font-pt-mono'
  })
}));

// Mock document.fonts API
(global as any).document.fonts = {
  ready: Promise.resolve(),
  addEventListener: () => {},
  removeEventListener: () => {}
};

// Mock event handling
const eventHandlers = new WeakMap();

// Add event handling methods to HTMLElement prototype
HTMLElement.prototype.attachEvent = function(event: string, handler: Function) {
  const normalizedEvent = event.replace(/^on/, '');
  if (!eventHandlers.has(this)) {
    eventHandlers.set(this, new Map());
  }
  eventHandlers.get(this).set(normalizedEvent, handler);
  this.addEventListener(normalizedEvent, handler as EventListener);
};

HTMLElement.prototype.detachEvent = function(event: string, handler: Function) {
  const normalizedEvent = event.replace(/^on/, '');
  if (eventHandlers.has(this)) {
    eventHandlers.get(this).delete(normalizedEvent);
  }
  this.removeEventListener(normalizedEvent, handler as EventListener);
};

// Create a custom event for propertychange
class PropertyChangeEvent extends Event {
  constructor(propertyName: string, oldValue: any, newValue: any) {
    super('propertychange');
    Object.defineProperties(this, {
      propertyName: { value: propertyName },
      oldValue: { value: oldValue },
      newValue: { value: newValue }
    });
  }
}

// Override value setter for input elements
const originalDescriptor = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value');
Object.defineProperty(HTMLInputElement.prototype, 'value', {
  get: function() {
    return originalDescriptor?.get?.call(this);
  },
  set: function(newValue) {
    const oldValue = this.value;
    originalDescriptor?.set?.call(this, newValue);
    const event = new PropertyChangeEvent('value', oldValue, newValue);
    this.dispatchEvent(event);
  },
  configurable: true,
  enumerable: true,
});
