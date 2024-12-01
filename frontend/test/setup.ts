import { afterEach, beforeAll, vi } from "bun:test";
import { cleanup } from '@testing-library/react';
import '@testing-library/jest-dom/matchers';
import { JSDOM } from 'jsdom';

// Create a new JSDOM instance
const dom = new JSDOM('<!doctype html><html><body></body></html>', {
  url: 'http://localhost',
  pretendToBeVisual: true
});

// Set up global variables
global.window = dom.window;
global.document = dom.window.document;
global.navigator = dom.window.navigator;

// Mock Next.js font
vi.mock('next/font/google', () => ({
  Plus_Jakarta_Sans: () => ({
    className: 'mocked-font',
    style: { fontFamily: 'mocked-font' }
  })
}));

// Mock canvas
class MockCanvas {
  getContext() {
    return {
      fillStyle: '',
      fillRect: () => {},
      clearRect: () => {},
      getImageData: () => ({
        data: new Uint8ClampedArray(0)
      }),
      putImageData: () => {},
      createImageData: () => {},
      setTransform: () => {},
      drawImage: () => {},
      save: () => {},
      restore: () => {},
      scale: () => {},
      rotate: () => {},
      translate: () => {},
      transform: () => {},
      beginPath: () => {},
      moveTo: () => {},
      lineTo: () => {},
      stroke: () => {},
      fill: () => {},
      arc: () => {},
      closePath: () => {}
    };
  }
}

// Mock HTMLCanvasElement
Object.defineProperty(global.window, 'HTMLCanvasElement', {
  value: class extends global.window.HTMLElement {
    getContext() {
      return new MockCanvas().getContext();
    }
  }
});

// Mock requestAnimationFrame
global.window.requestAnimationFrame = callback => setTimeout(callback, 0);
global.window.cancelAnimationFrame = id => clearTimeout(id);

// Mock ResizeObserver
global.window.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock IntersectionObserver
global.window.IntersectionObserver = class IntersectionObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock matchMedia
global.window.matchMedia = query => ({
  matches: false,
  media: query,
  onchange: null,
  addListener: () => {},
  removeListener: () => {},
  addEventListener: () => {},
  removeEventListener: () => {},
  dispatchEvent: () => false,
});

beforeAll(() => {
  // Additional setup if needed
});

afterEach(() => {
  cleanup();
  // Reset the body
  document.body.innerHTML = '';
});
