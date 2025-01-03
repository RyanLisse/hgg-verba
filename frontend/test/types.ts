declare module "bun:test" {
  interface Matchers<R> {
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