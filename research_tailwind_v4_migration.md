# Tailwind CSS v4 Migration Guide for Next.js 14

Generated: 2025-01-07

Sources: Tailwind CSS Official Docs, GitHub Discussions, Community Guides

## Quick Reference

**Key Points:**

- **Browser Requirements**: Safari 16.4+, Chrome 111+, Firefox 128+
  (uses @property and color-mix())
- **Major Breaking Change**: Dark mode implementation completely redesigned
  with CSS variables
- **Performance Boost**: 3.5x faster full rebuilds, 8x faster incremental builds
- **Migration Tool Available**: `npx @tailwindcss/upgrade` automates most changes
- **Vite Integration**: New dedicated `@tailwindcss/vite` plugin recommended
  over PostCSS

## Overview

Tailwind CSS v4 represents a major architectural shift to a CSS-first
configuration approach with native CSS variables, improved performance, and
simplified integration. While offering significant benefits, the migration
requires careful attention to breaking changes, especially around dark mode
implementation and utility class updates.

## Implementation Details

### 1. Installation and Setup

**Current Setup Migration:**

```bash
# Install v4 packages
npm install tailwindcss@next @tailwindcss/vite@next
```

**CSS Import Changes:**

```css
/* v3 approach (remove) */
@tailwind base;
@tailwind components; 
@tailwind utilities;

/* v4 approach (new) */
@import "tailwindcss";
```

**Vite Configuration Update:**

```typescript
// vite.config.ts
import { defineConfig } from "vite";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [
    tailwindcss(), // New dedicated plugin
  ],
});
```

**PostCSS Configuration (if not using Vite plugin):**

```javascript
// postcss.config.mjs
export default {
  plugins: {
    "@tailwindcss/postcss": {}, // New package
    // Remove: postcss-import and autoprefixer (built-in now)
  },
};
```

### 2. Dark Mode Implementation Overhaul

**v4 CSS Variable Approach:**

```css
@import "tailwindcss";

/* Define custom dark mode variant */
@variant dark (&:where([data-theme="dark"] *));

/* Theme configuration with CSS variables */
@theme {
  --color-background: light-dark(white, #0a0a0a);
  --color-foreground: light-dark(#0a0a0a, white);
  --color-primary: light-dark(#0066cc, #3399ff);
}
```

**Next.js with next-themes Integration:**

```typescript
// app/layout.tsx
import { ThemeProvider } from 'next-themes'

export default function RootLayout({ children }) {
  return (
    <html suppressHydrationWarning>
      <body>
        <ThemeProvider attribute="data-theme" defaultTheme="system">
          {children}
        </ThemeProvider>
      </body>
    </html>
  )
}
```

### 3. Utility Class Updates

**Shadow/Radius/Blur Scale Changes:**

```html
<!-- v3 → v4 updates -->
<input class="shadow-sm" />     → <input class="shadow-xs" />
<input class="shadow" />        → <input class="shadow-sm" />
<input class="rounded-sm" />    → <input class="rounded-xs" />
```

**Outline Utility Changes:**

```html
<!-- v3 → v4 updates -->
<input class="focus:outline-none" />     → <input class="focus:outline-hidden" />
<input class="outline outline-2" />      → <input class="outline-2" />
```

**Ring Utility Default Changes:**

```html
<!-- v3 → v4 updates (default width: 3px → 1px) -->
<input class="ring ring-blue-500" />     → <input class="ring-3 ring-blue-500" />
```

**Border Color Default Changes:**

```html
<!-- v4 defaults to currentColor instead of gray-200 -->
<div class="border px-2 py-3">           
→ <div class="border border-gray-200 px-2 py-3">
```

### 4. Custom Properties Integration

**CSS Variable Access:**

```css
/* Direct CSS variable usage (recommended) */
.my-component {
  background-color: var(--color-blue-500);
  border-radius: var(--radius-lg);
}

/* theme() function (legacy, still supported) */
.my-component {
  background-color: theme(--color-blue-500);
}
```

**Animation Library Integration:**

```jsx
// Motion.dev/Framer Motion with CSS variables
<motion.div 
  animate={{ 
    backgroundColor: "var(--color-blue-500)",
    scale: 1.1 
  }} 
/>
```

### 5. Custom Utilities with @utility API

**Replace @layer utilities:**

```css
/* v3 approach */
@layer utilities {
  .tab-4 {
    tab-size: 4;
  }
}

/* v4 approach */
@utility tab-4 {
  tab-size: 4;
}

/* Dynamic utilities */
@utility tab-* {
  tab-size: --value(integer);
}
```

### 6. Container Customization

**Replace removed config options:**

```css
/* v4 container customization */
@utility container {
  margin-inline: auto;
  padding-inline: 2rem;
}
```

## Important Considerations

**Warning Areas:**

- **Browser Support**: v4 requires modern browsers (Safari 16.4+, Chrome 111+,
  Firefox 128+)
- **Radix UI Compatibility**: Remove `tailwindcss-animate` plugin - may conflict
  with v4's CSS variable architecture
- **Dark Mode Breaking**: Complete reimplementation - existing dark mode
  implementations will break
- **Space Utilities**: Selector changes may affect layouts using `space-y-*`
  or `space-x-*`
- **Button Cursor**: Default changed from `pointer` to `default` - may need
  explicit restoration
- **Hover Behavior**: Now only applies when primary input supports hover
  (affects touch devices)
- **Variable Syntax**: Arbitrary values using CSS variables now use `()`
  instead of `[]`: `bg-(--brand-color)`
- **Gradient Overrides**: Behavior improved but may require `via-none` to reset
  three-stop gradients

## Recommended Migration Strategy

### Phase 1: Preparation & Assessment

```bash
# 1. Check browser support requirements
# 2. Audit existing dark mode implementation
# 3. Review custom CSS using @layer or @apply
# 4. Backup current working state
git checkout -b tailwind-v4-migration
```

### Phase 2: Automated Migration

```bash
# Run official upgrade tool (requires Node.js 20+)
npx @tailwindcss/upgrade

# Review generated changes carefully
git diff
```

### Phase 3: Manual Fixes & Testing

1. **Update dark mode implementation** with new CSS variable approach
2. **Fix utility class name changes** (shadow, outline, ring, etc.)
3. **Update Radix UI integration** (remove tailwindcss-animate)
4. **Test across target browsers** and devices
5. **Verify custom animations** and component libraries

### Phase 4: Performance Optimization

1. **Leverage CSS variables** for dynamic theming
2. **Remove unnecessary PostCSS plugins** (import, autoprefixer)
3. **Migrate to Vite plugin** if using PostCSS approach
4. **Update build scripts** for new CLI package

## Resources

**References:**

- [Tailwind CSS v4 Upgrade Guide](https://tailwindcss.com/docs/upgrade-guide) -
  Official migration documentation
- [Tailwind CSS v4 Announcement](https://tailwindcss.com/blog/tailwindcss-v4) -
  Architecture overview and benefits
- [Next.js 14 with Tailwind v4 Guide](https://www.thingsaboutweb.dev/en/posts/dark-mode-with-tailwind-v4-nextjs)
  - Dark mode implementation
- [GitHub Discussion: v4 Migration Issues](https://github.com/tailwindlabs/tailwindcss/discussions/16517)
  - Community troubleshooting
- [Tailwind v4 Alpha Documentation](https://tailwindcss.com/blog/tailwindcss-v4-alpha)
  - Early feature previews

## PR Strategy Recommendations

### Split Migration into Focused PRs

#### PR 1: Infrastructure Updates

- Package updates and configuration changes
- PostCSS/Vite plugin migration
- CSS import updates
- Basic utility class name fixes

#### PR 2: Dark Mode Reimplementation

- New CSS variable approach
- Theme provider updates
- Component dark mode fixes
- Theme switching functionality

#### PR 3: Component Library Updates

- Radix UI compatibility fixes
- Remove tailwindcss-animate conflicts
- Custom animation migrations
- Third-party integration updates

#### PR 4: Performance & Polish

- CSS variable optimizations
- Bundle size analysis
- Cross-browser testing fixes
- Documentation updates

## Metadata

- **Research Date**: 2025-01-07
- **Confidence**: High
- **Version Checked**: 4.0.0-beta.3
- **Browser Requirements**: Safari 16.4+, Chrome 111+, Firefox 128+
- **Migration Complexity**: High
- **Recommended Approach**: Phased Migration
