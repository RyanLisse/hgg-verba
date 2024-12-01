import { beforeAll, expect } from "@jest/globals";
import { JSDOM } from 'jsdom';

// Set up DOM environment
const dom = new JSDOM('<!doctype html><html><body></body></html>', {
  url: 'http://localhost',
  pretendToBeVisual: true,
});

// Set up global DOM environment
(global as any).document = dom.window.document;
(global as any).window = dom.window;
(global as any).navigator = dom.window.navigator;
(global as any).HTMLElement = dom.window.HTMLElement;
(global as any).Element = dom.window.Element;
(global as any).getComputedStyle = dom.window.getComputedStyle;

// Mock Next.js font
const mockFont = () => ({
  className: 'plus-jakarta-sans',
  style: { fontFamily: 'Plus_Jakarta_Sans' },
});

(require.cache as any)[require.resolve('next/font/google')] = {
  id: 'next/font/google',
  filename: 'next/font/google',
  loaded: true,
  exports: {
    Plus_Jakarta_Sans: mockFont
  }
};

// Mock router
(require.cache as any)[require.resolve('next/router')] = {
  id: 'next/router',
  filename: 'next/router',
  loaded: true,
  exports: {
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
  }
};

// Mock navigation
(require.cache as any)[require.resolve('next/navigation')] = {
  id: 'next/navigation',
  filename: 'next/navigation',
  loaded: true,
  exports: {
    useRouter: () => ({
      push: () => {},
      replace: () => {},
      prefetch: () => {},
    }),
    useSearchParams: () => ({
      get: () => {},
    }),
    usePathname: () => ''
  }
};

interface CustomMatchers {
  toBeInTheDocument(): { pass: boolean; message: () => string };
  toHaveClass(...args: string[]): { pass: boolean; message: () => string };
  toHaveAttribute(attr: string, value?: string): { pass: boolean; message: () => string };
  toHaveTextContent(text: string): { pass: boolean; message: () => string };
  toBeDisabled(): { pass: boolean; message: () => string };
  toHaveLength(length: number): { pass: boolean; message: () => string };
  toHaveBeenCalledWith(...args: any[]): { pass: boolean; message: () => string };
  toHaveBeenCalledTimes(times: number): { pass: boolean; message: () => string };
  toHaveBeenLastCalledWith(...args: any[]): { pass: boolean; message: () => string };
}

// Add custom matchers
const customMatchers: CustomMatchers = {
  toBeInTheDocument(): { pass: boolean; message: () => string } {
    return {
      pass: this.actual !== null && this.actual !== undefined,
      message: () => `expected ${this.actual} to be in the document`,
    };
  },
  toHaveClass(...args: string[]): { pass: boolean; message: () => string } {
    const classList = this.actual.className?.split(' ') || [];
    return {
      pass: args.every(cls => classList.includes(cls)),
      message: () => `expected ${this.actual} to have classes ${args.join(', ')}`,
    };
  },
  toHaveAttribute(attr: string, value?: string): { pass: boolean; message: () => string } {
    const hasAttr = this.actual.hasAttribute(attr);
    if (value === undefined) {
      return {
        pass: hasAttr,
        message: () => `expected ${this.actual} to have attribute ${attr}`,
      };
    }
    return {
      pass: this.actual.getAttribute(attr) === value,
      message: () => `expected ${this.actual} to have attribute ${attr} with value ${value}`,
    };
  },
  toHaveTextContent(text: string): { pass: boolean; message: () => string } {
    return {
      pass: this.actual.textContent === text,
      message: () => `expected ${this.actual} to have text content ${text}`,
    };
  },
  toBeDisabled(): { pass: boolean; message: () => string } {
    return {
      pass: this.actual.disabled,
      message: () => `expected ${this.actual} to be disabled`,
    };
  },
  toHaveLength(length: number): { pass: boolean; message: () => string } {
    return {
      pass: this.actual.length === length,
      message: () => `expected ${this.actual} to have length ${length}`,
    };
  },
  toHaveBeenCalledWith(...args: any[]): { pass: boolean; message: () => string } {
    return {
      pass: this.actual.mock.calls[0] === args,
      message: () => `expected ${this.actual} to have been called with ${args}`,
    };
  },
  toHaveBeenCalledTimes(times: number): { pass: boolean; message: () => string } {
    return {
      pass: this.actual.mock.calls.length === times,
      message: () => `expected ${this.actual} to have been called ${times} times`,
    };
  },
  toHaveBeenLastCalledWith(...args: any[]): { pass: boolean; message: () => string } {
    const lastCall = this.actual.mock.calls[this.actual.mock.calls.length - 1];
    return {
      pass: lastCall === args,
      message: () => `expected ${this.actual} to have been last called with ${args}`,
    };
  },
};

// Add custom matchers to expect
(expect as any).extend(customMatchers);
