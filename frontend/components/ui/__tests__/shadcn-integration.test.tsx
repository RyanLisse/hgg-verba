import { render, screen } from '@testing-library/react';
import { Button } from '../button';
import { Avatar, AvatarFallback } from '../avatar';
import { ScrollArea } from '../scroll-area';

describe('shadcn/ui Integration', () => {
  it('renders Button component with Verba variant', () => {
    render(<Button variant="verba">Test Button</Button>);
    const button = screen.getByRole('button', { name: 'Test Button' });
    expect(button).toBeInTheDocument();
    expect(button).toHaveClass('bg-button-verba');
  });

  it('renders Avatar component with fallback', () => {
    render(
      <Avatar>
        <AvatarFallback>TB</AvatarFallback>
      </Avatar>
    );
    const fallback = screen.getByText('TB');
    expect(fallback).toBeInTheDocument();
  });

  it('renders ScrollArea component', () => {
    render(
      <ScrollArea className="h-32 w-32">
        <div>Scrollable content</div>
      </ScrollArea>
    );
    const content = screen.getByText('Scrollable content');
    expect(content).toBeInTheDocument();
  });

  it('Button component works with different variants', () => {
    const { rerender } = render(<Button variant="default">Default</Button>);
    expect(screen.getByRole('button')).toHaveClass('bg-primary');
    
    rerender(<Button variant="verba-primary">Verba Primary</Button>);
    expect(screen.getByRole('button')).toHaveClass('bg-primary-verba');
    
    rerender(<Button variant="verba-secondary">Verba Secondary</Button>);
    expect(screen.getByRole('button')).toHaveClass('bg-secondary-verba');
  });
});