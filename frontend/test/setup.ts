import { beforeAll, expect } from "bun:test";
import { JSDOM } from 'jsdom';

// Set up DOM environment
const dom = new JSDOM('<!doctype html><html><body></body></html>', {
  url: 'http://localhost',
  pretendToBeVisual: true,
});

global.document = dom.window.document;
global.window = dom.window;
global.navigator = dom.window.navigator;
global.HTMLElement = dom.window.HTMLElement;
global.Element = dom.window.Element;
global.getComputedStyle = dom.window.getComputedStyle;

// Mock Next.js font
const mockFont = () => ({
  className: 'plus-jakarta-sans',
  style: { fontFamily: 'Plus_Jakarta_Sans' },
});

require.cache[require.resolve('next/font/google')] = {
  id: 'next/font/google',
  filename: 'next/font/google',
  loaded: true,
  exports: {
    Plus_Jakarta_Sans: mockFont
  }
};

// Mock router
require.cache[require.resolve('next/router')] = {
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
require.cache[require.resolve('next/navigation')] = {
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
  expectResult.toBeInTheDocument = () => {
    return originalExpect(actual !== null && actual !== undefined).toBe(true);
  };

  expectResult.toHaveClass = (...args: string[]) => {
    const classList = actual.className?.split(' ') || [];
    return originalExpect(args.every(cls => classList.includes(cls))).toBe(true);
  };

  expectResult.toHaveAttribute = (attr: string, value?: string) => {
    const hasAttr = actual.hasAttribute(attr);
    if (value === undefined) {
      return originalExpect(hasAttr).toBe(true);
    }
    return originalExpect(actual.getAttribute(attr)).toBe(value);
  };

  expectResult.toHaveTextContent = (text: string) => {
    return originalExpect(actual.textContent).toBe(text);
  };

  expectResult.toBeDisabled = () => {
    return originalExpect(actual.disabled).toBe(true);
  };

  expectResult.toHaveLength = (length: number) => {
    return originalExpect(actual.length).toBe(length);
  };

  expectResult.toHaveBeenCalledWith = (...args: any[]) => {
    return originalExpect(actual.mock.calls[0]).toEqual(args);
  };

  expectResult.toHaveBeenCalledTimes = (times: number) => {
    return originalExpect(actual.mock.calls.length).toBe(times);
  };

  expectResult.toHaveBeenLastCalledWith = (...args: any[]) => {
    const lastCall = actual.mock.calls[actual.mock.calls.length - 1];
    return originalExpect(lastCall).toEqual(args);
  };

  // Add negated matchers
  expectResult.not = {
    ...expectResult.not,
    toBeDisabled: () => {
      return originalExpect(actual.disabled).toBe(false);
    },
    toBeInTheDocument: () => {
      return originalExpect(actual === null || actual === undefined).toBe(true);
    },
    toHaveClass: (...args: string[]) => {
      const classList = actual.className?.split(' ') || [];
      return originalExpect(args.some(cls => !classList.includes(cls))).toBe(true);
    },
  };

  return expectResult;
}

// Create a proxy to handle property access
const expectProxy = new Proxy(extendExpect, {
  get(target, prop) {
    if (prop === 'extend') {
      return target.extend;
    }
    return originalExpect[prop];
  },
  apply(target, thisArg, args) {
    return target.apply(thisArg, args);
  },
});

// Add static properties from original expect
Object.entries(originalExpect).forEach(([key, value]) => {
  if (typeof value === 'function') {
    expectProxy[key] = value.bind(originalExpect);
  } else {
    expectProxy[key] = value;
  }
});

// Add custom matchers to expect prototype
const customMatchers = {
  toBeInTheDocument() {
    return originalExpect(this !== null && this !== undefined).toBe(true);
  },
  toHaveClass(...args: string[]) {
    const classList = this.className?.split(' ') || [];
    return originalExpect(args.every(cls => classList.includes(cls))).toBe(true);
  },
  toHaveAttribute(attr: string, value?: string) {
    const hasAttr = this.hasAttribute(attr);
    if (value === undefined) {
      return originalExpect(hasAttr).toBe(true);
    }
    return originalExpect(this.getAttribute(attr)).toBe(value);
  },
  toHaveTextContent(text: string) {
    return originalExpect(this.textContent).toBe(text);
  },
  toBeDisabled() {
    return originalExpect(this.disabled).toBe(true);
  },
  toHaveLength(length: number) {
    return originalExpect(this.length).toBe(length);
  },
  toHaveBeenCalledWith(...args: any[]) {
    return originalExpect(this.mock.calls[0]).toEqual(args);
  },
  toHaveBeenCalledTimes(times: number) {
    return originalExpect(this.mock.calls.length).toBe(times);
  },
  toHaveBeenLastCalledWith(...args: any[]) {
    const lastCall = this.mock.calls[this.mock.calls.length - 1];
    return originalExpect(lastCall).toEqual(args);
  },
};

// Add custom matchers to expect prototype
Object.entries(customMatchers).forEach(([key, value]) => {
  Object.defineProperty(expectProxy.prototype, key, {
    value,
    configurable: true,
    writable: true,
    enumerable: true,
  });
});

// Add negated matchers to expect prototype
const negatedMatchers = {
  toBeDisabled() {
    return originalExpect(this.disabled).toBe(false);
  },
  toBeInTheDocument() {
    return originalExpect(this === null || this === undefined).toBe(true);
  },
  toHaveClass(...args: string[]) {
    const classList = this.className?.split(' ') || [];
    return originalExpect(args.some(cls => !classList.includes(cls))).toBe(true);
  },
};

// Add negated matchers to expect prototype
Object.entries(negatedMatchers).forEach(([key, value]) => {
  Object.defineProperty(expectProxy.prototype.not, key, {
    value,
    configurable: true,
    writable: true,
    enumerable: true,
  });
});

(global as any).expect = expectProxy;
