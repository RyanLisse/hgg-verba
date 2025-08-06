// Simple example showing shadcn/ui components work with Verba styling
import React from "react";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { ScrollArea } from "@/components/ui/scroll-area";

export function ShadcnExample() {
  return (
    <div className="p-4 space-y-4">
      <h2 className="text-xl font-semibold text-text-verba">shadcn/ui + Verba Example</h2>
      
      {/* Example showing Verba-themed buttons */}
      <div className="flex gap-2">
        <Button variant="verba">Verba Button</Button>
        <Button variant="verba-primary">Primary</Button>
        <Button variant="verba-secondary">Secondary</Button>
      </div>

      {/* Example showing avatar with Verba theming */}
      <div className="flex items-center gap-2">
        <Avatar className="border-2 border-primary-verba">
          <AvatarImage src="/verba.png" alt="Verba" />
          <AvatarFallback className="bg-primary-verba text-text-verba">V</AvatarFallback>
        </Avatar>
        <span className="text-text-verba">User Avatar</span>
      </div>

      {/* Example showing scroll area with content */}
      <ScrollArea className="h-24 w-full border border-border rounded-md p-2 bg-bg-alt-verba">
        <div className="text-sm text-text-alt-verba">
          This is scrollable content that demonstrates the ScrollArea component working with Verba's color scheme.
          {Array.from({ length: 10 }, (_, i) => (
            <div key={i}>Line {i + 1} of scrollable content</div>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}