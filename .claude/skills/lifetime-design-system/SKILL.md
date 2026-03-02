---
name: lifetime-design-system
description: Use when adding styles, working with colors or spacing, implementing dark mode, handling responsive layouts, or using CSS custom properties in the Lifetime Calendar frontend.
---

# Lifetime Calendar — Design System Reference

## CSS Architecture

All styling uses CSS custom properties — no Tailwind, no CSS-in-JS.

**Import chain:** `design-system.css` → `base.css` → `main.css` → `main.js`
All CSS variables are globally available in every component.

## CSS Variable Groups (`assets/design-system.css`)

| Variable group | Examples |
|---|---|
| `--color-primary-*` | 50–950 scale, sky-blue palette |
| `--color-success-*` | green — lived weeks |
| `--color-warning-*` | amber — current week |
| `--color-error-*` | red — errors |
| `--color-neutral-*` | gray scale |
| `--color-text-*` | `primary`, `secondary`, `tertiary`, `inverse` |
| `--color-background*` | `background`, `background-secondary`, `background-tertiary` |
| `--color-surface` | card/modal background |
| `--color-border` | borders |
| `--glass-bg/border/blur` | glassmorphism values |
| `--space-{1–32}` | spacing scale (0.25rem steps) |
| `--radius-{sm–full}` | border-radius scale |
| `--shadow-{sm–2xl}` | box-shadow scale |
| `--duration-{fast/normal/slow}` | 150ms / 250ms / 350ms |
| `--ease-{in/out/in-out}` | cubic-bezier curves |
| `--font-size-{xs–5xl}` | type scale |
| `--font-weight-{normal–bold}` | 400 / 500 / 600 / 700 |

## Theme Switching

- `:root` defines light-mode defaults
- `[data-theme="dark"]` and `[data-theme="light"]` override **semantic tokens** only: `--color-background`, `--color-surface`, `--color-text-*`, `--glass-*`, `--shadow-*`
- Accent palette (`--color-primary-*`, `--color-success-*`, etc.) is **theme-invariant**
- **Never** add `[data-theme="dark"]` blocks inside component `<style scoped>` — theme adaptation is handled entirely by `design-system.css`

## Rules for Using Design Tokens

**Always use tokens, never raw values:**
```css
/* Correct */
color: var(--color-success-600);
padding: var(--space-3);

/* Wrong — bypasses theme system */
color: #22c55e;
padding: 12px;
```

**Prefer semantic tokens over palette tokens in components:**
```css
/* Correct — adapts to theme */
color: var(--color-text-secondary);

/* Avoid — always neutral-600, wrong in dark mode */
color: var(--color-neutral-600);
```

**Keep `<style scoped>` for component-specific styles.**
Don't override child scoped styles from a parent using `:deep()` — it breaks encapsulation.

## Responsive Breakpoints

| Breakpoint | Behavior |
|---|---|
| `>768px` | Default desktop layout |
| `≤768px` | 2-column stats grid, smaller week boxes (`max(6px, min(1vw, 10px))`), modal footer stacks vertically |
| `≤480px` | 1-column stats grid, smallest week boxes (`max(4px, min(0.8vw, 6px))`) |

## Reduced Motion

`@media (prefers-reduced-motion: reduce)` sets **all duration variables to `0s`**, disabling all transitions and animations globally — handled in `design-system.css`, no per-component handling needed.

## Accessibility Conventions

- All interactive elements must be keyboard-reachable (`tabindex="0"` + `@keydown.enter`/`@keydown.space`)
- Prefer `<button>` for actions (gets keyboard behavior for free)
- `aria-label` on icon-only controls — describe the *action*: `"Switch to dark mode"`, not `"Moon icon"`
- `role="status" aria-live="polite"` on loading and error state containers
- Modals should trap focus: move focus to first focusable element on open, restore to trigger on close
