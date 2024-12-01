import { beforeAll, expect } from "bun:test";
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

// Add custom matchers
const originalExpect = expect;

function extendExpect(actual: any) {
  const expectResult = originalExpect(actual);

  // Add custom matchers
  const customMatchers = {
    toBeInTheDocument() {
      return originalExpect(actual !== null && actual !== undefined).toBe(true);
    },
    toHaveClass(...args: string[]) {
      const classList = actual.className?.split(' ') || [];
      return originalExpect(args.every(cls => classList.includes(cls))).toBe(true);
    },
    toHaveAttribute(attr: string, value?: string) {
      const hasAttr = actual.hasAttribute(attr);
      if (value === undefined) {
        return originalExpect(hasAttr).toBe(true);
      }
      return originalExpect(actual.getAttribute(attr)).toBe(value);
    },
    toHaveTextContent(text: string) {
      return originalExpect(actual.textContent).toBe(text);
    },
    toBeDisabled() {
      return originalExpect(actual.disabled).toBe(true);
    },
    toHaveLength(length: number) {
      return originalExpect(actual.length).toBe(length);
    },
    toHaveBeenCalledWith(...args: any[]) {
      return originalExpect(actual.mock.calls[0]).toEqual(args);
    },
    toHaveBeenCalledTimes(times: number) {
      return originalExpect(actual.mock.calls.length).toBe(times);
    },
    toHaveBeenLastCalledWith(...args: any[]) {
      const lastCall = actual.mock.calls[actual.mock.calls.length - 1];
      return originalExpect(lastCall).toEqual(args);
    },
  };

  // Add negated matchers
  const negatedMatchers = {
    toBeDisabled() {
      return originalExpect(actual.disabled).toBe(false);
    },
    toBeInTheDocument() {
      return originalExpect(actual === null || actual === undefined).toBe(true);
    },
    toHaveClass(...args: string[]) {
      const classList = actual.className?.split(' ') || [];
      return originalExpect(args.some(cls => !classList.includes(cls))).toBe(true);
    },
  };

  // Add custom matchers to expectResult
  Object.entries(customMatchers).forEach(([key, value]) => {
    (expectResult as any)[key] = value;
  });

  // Add negated matchers to expectResult.not
  expectResult.not = {
    ...expectResult.not,
    ...negatedMatchers,
  };

  return expectResult;
}

// Create a proxy to handle property access
const expectProxy = new Proxy(extendExpect, {
  get(target: any, prop: string) {
    return originalExpect[prop];
  },
  apply(target: any, thisArg: any, args: any[]) {
    return target.apply(thisArg, args);
  },
}) as typeof expect;

(global as any).expect = expectProxy;
