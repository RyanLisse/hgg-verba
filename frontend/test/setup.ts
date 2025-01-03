import { beforeAll, expect } from "bun:test";
import { JSDOM } from 'jsdom';
import { configure } from '@testing-library/react';

// Set up DOM environment
const dom = new JSDOM('<!doctype html><html><body></body></html>', {
  url: 'http://localhost',
  pretendToBeVisual: true,
  runScripts: 'dangerously',
});

// Set up global DOM environment
(global as any).window = dom.window;
(global as any).document = dom.window.document;
(global as any).navigator = dom.window.navigator;
(global as any).HTMLElement = dom.window.HTMLElement;
(global as any).Element = dom.window.Element;
(global as any).getComputedStyle = dom.window.getComputedStyle;
(global as any).MutationObserver = dom.window.MutationObserver;

// Configure testing library
configure({
  testIdAttribute: 'data-testid',
});

// Mock window properties
Object.defineProperty(dom.window, 'matchMedia', {
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

Object.defineProperty(dom.window, 'ResizeObserver', {
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

// Mock Next.js font
const mockFont = () => ({
  className: 'plus-jakarta-sans',
  style: { fontFamily: 'Plus_Jakarta_Sans' },
});

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
require.cache[require.resolve('next/font/google')] = mockModule('next/font/google', {
  Plus_Jakarta_Sans: mockFont,
  Inter: mockFont,
  Open_Sans: mockFont,
  PT_Mono: mockFont
});

require.cache[require.resolve('next/router')] = mockModule('next/router', {
  useRouter: () => ({
    route: '/',
    pathname: '',
    query: '',
    asPath: '',
    push: () => {},
    events: {
      on: () => {},
      off: () => {},
    },
    beforePopState: () => {},
    prefetch: () => {},
  })
});

require.cache[require.resolve('next/navigation')] = mockModule('next/navigation', {
  useRouter: () => ({
    push: () => {},
    replace: () => {},
    prefetch: () => {},
  }),
  useSearchParams: () => ({
    get: () => {},
  }),
  usePathname: () => ''
});

// Add custom matchers
expect.extend({
  toBeInTheDocument(received: any) {
    return {
      pass: received !== null && received !== undefined,
      message: () => `expected ${received} ${this.isNot ? 'not ' : ''}to be in the document`,
    };
  },
  toHaveClass(received: any, ...classes: string[]) {
    const classList = received?.className?.split(' ') || [];
    return {
      pass: classes.every(cls => classList.includes(cls)),
      message: () => `expected ${received} ${this.isNot ? 'not ' : ''}to have classes ${classes.join(', ')}`,
    };
  },
  toHaveAttribute(received: any, attr: string, value?: string) {
    const hasAttr = received?.hasAttribute(attr);
    if (value === undefined) {
      return {
        pass: hasAttr,
        message: () => `expected ${received} ${this.isNot ? 'not ' : ''}to have attribute ${attr}`,
      };
    }
    return {
      pass: received?.getAttribute(attr) === value,
      message: () => `expected ${received} ${this.isNot ? 'not ' : ''}to have attribute ${attr} with value ${value}`,
    };
  },
  toHaveTextContent(received: any, text: string) {
    return {
      pass: received?.textContent === text,
      message: () => `expected ${received} ${this.isNot ? 'not ' : ''}to have text content ${text}`,
    };
  },
  toBeDisabled(received: any) {
    return {
      pass: received?.disabled === true,
      message: () => `expected ${received} ${this.isNot ? 'not ' : ''}to be disabled`,
    };
  },
  toHaveLength(received: any, length: number) {
    return {
      pass: received?.length === length,
      message: () => `expected ${received} ${this.isNot ? 'not ' : ''}to have length ${length}`,
    };
  },
  toHaveBeenCalledWith(received: any, ...args: any[]) {
    const calls = received?.mock?.calls || [];
    return {
      pass: calls[0]?.every((arg: any, i: number) => arg === args[i]) ?? false,
      message: () => `expected ${received} ${this.isNot ? 'not ' : ''}to have been called with ${args.join(', ')}`,
    };
  },
  toHaveBeenCalledTimes(received: any, times: number) {
    const calls = received?.mock?.calls || [];
    return {
      pass: calls.length === times,
      message: () => `expected ${received} ${this.isNot ? 'not ' : ''}to have been called ${times} times`,
    };
  },
  toHaveBeenLastCalledWith(received: any, ...args: any[]) {
    const calls = received?.mock?.calls || [];
    const lastCall = calls[calls.length - 1] || [];
    return {
      pass: lastCall.every((arg: any, i: number) => arg === args[i]) ?? false,
      message: () => `expected ${received} ${this.isNot ? 'not ' : ''}to have been last called with ${args.join(', ')}`,
    };
  },
});
