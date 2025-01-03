import { expect, test, mock } from "bun:test";
import { JSDOM } from 'jsdom';

const dom = new JSDOM('<!DOCTYPE html><html><body></body></html>', {
  url: 'http://localhost',
  pretendToBeVisual: true,
});

declare global {
  var window: typeof dom.window;
  var document: typeof dom.window.document;
  var navigator: typeof dom.window.navigator;
  var HTMLElement: typeof dom.window.HTMLElement;
}

global.window = dom.window;
global.document = dom.window.document;
global.navigator = dom.window.navigator;
global.HTMLElement = dom.window.HTMLElement;

Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: mock(() => ({
    matches: false,
    media: '',
    onchange: null,
    addListener: mock(),
    removeListener: mock(),
    addEventListener: mock(),
    removeEventListener: mock(),
    dispatchEvent: mock(),
  })),
});

Object.defineProperty(window, 'ResizeObserver', {
  writable: true,
  value: mock(() => ({
    observe: mock(),
    unobserve: mock(),
    disconnect: mock(),
  })),
}); 