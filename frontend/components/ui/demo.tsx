import React from "react";
import { Button } from "./button";
import { Avatar, AvatarFallback, AvatarImage } from "./avatar";
import { ScrollArea } from "./scroll-area";

// Demo component to test shadcn components work alongside existing daisyui
export function ShadcnDemo() {
  return (
    <div className="p-4 space-y-4 bg-bg-verba">
      <h2 className="text-2xl font-bold text-text-verba">shadcn/ui + Verba Integration Demo</h2>
      
      {/* Button variants test */}
      <div className="space-y-2">
        <h3 className="text-lg font-semibold">Button Variants:</h3>
        <div className="flex gap-2 flex-wrap">
          <Button variant="default">Default</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="outline">Outline</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="verba">Verba Style</Button>
          <Button variant="verba-primary">Verba Primary</Button>
          <Button variant="verba-secondary">Verba Secondary</Button>
          <Button variant="verba-warning">Verba Warning</Button>
        </div>
      </div>

      {/* Avatar test */}
      <div className="space-y-2">
        <h3 className="text-lg font-semibold">Avatar Component:</h3>
        <div className="flex gap-2">
          <Avatar>
            <AvatarImage src="/verba.png" alt="Verba" />
            <AvatarFallback>V</AvatarFallback>
          </Avatar>
          <Avatar>
            <AvatarFallback className="bg-primary-verba text-text-verba">UI</AvatarFallback>
          </Avatar>
        </div>
      </div>

      {/* ScrollArea test */}
      <div className="space-y-2">
        <h3 className="text-lg font-semibold">Scroll Area Component:</h3>
        <ScrollArea className="h-32 w-full border border-border rounded-md p-4">
          <div className="space-y-2">
            {Array.from({ length: 20 }, (_, i) => (
              <div key={i} className="text-sm">
                Scrollable item {i + 1} - This demonstrates the ScrollArea component working with Verba styles.
              </div>
            ))}
          </div>
        </ScrollArea>
      </div>

      {/* DaisyUI compatibility test */}
      <div className="space-y-2">
        <h3 className="text-lg font-semibold">DaisyUI Compatibility:</h3>
        <div className="flex gap-2 items-center">
          <Button variant="verba">shadcn Button</Button>
          <button className="btn btn-primary">DaisyUI Button</button>
          <div className="badge badge-secondary">DaisyUI Badge</div>
        </div>
      </div>
    </div>
  );
}