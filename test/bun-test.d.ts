declare module "bun:test" {
  export function expect(value: any): any;
  export function test(name: string, fn: () => void | Promise<void>): void;
  export function mock<T extends (...args: any[]) => any>(
    implementation?: T
  ): {
    (...args: Parameters<T>): ReturnType<T>;
    mock: {
      calls: Parameters<T>[];
      results: { type: "return" | "throw"; value: any }[];
      instances: any[];
      lastCall: Parameters<T>;
    };
  };
  export function beforeAll(fn: () => void | Promise<void>): void;
  export function afterAll(fn: () => void | Promise<void>): void;
  export function beforeEach(fn: () => void | Promise<void>): void;
  export function afterEach(fn: () => void | Promise<void>): void;
  export function describe(name: string, fn: () => void): void;
  export function it(name: string, fn: () => void | Promise<void>): void;
} 