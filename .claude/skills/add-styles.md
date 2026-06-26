---
name: add-styles
description: Apply Tailwind CSS + DaisyUI styling to an existing Vue component without changing its logic. Use when the user asks to style, restyle, or polish an existing component or view.
user-invocable: true
allowed-tools:
  - Read
  - Edit
  - Glob
  - Grep
---

# /add-styles — Style an Existing Component

Apply Tailwind + DaisyUI styles to `$ARGUMENTS`. **Do not change the component's logic**
(script block, props, emits, data flow) — only its template classes and markup structure.

## Rules

- DaisyUI components first: `btn`, `card`, `badge`, `input`, `alert`, `progress`, `modal`
- Tailwind for layout/spacing only: `flex`, `grid`, `gap-*`, `p-*`, `rounded-*`, `max-w-md`
- Dark theme tokens only — `bg-base-100/200/300`, `text-base-content`, and the semantic
  `primary`/`secondary`/`accent`/`success`/`info`/`warning`/`error`
- Never hardcode a color (`bg-blue-500`) where a DaisyUI token covers it
- Mobile-first: style for 375 px first, add `sm:` / `md:` only for larger screens
- No horizontal scroll at 375 px; interactive elements get the `tap-target` utility (≥44 px)
- Reuse the project surfaces: `surface` / `surface-soft` (defined in `src/style.css`)
- Respect `prefers-reduced-motion` for any animation

## Workflow

1. Read the component and identify the template only.
2. Apply classes; keep the `<script setup>` untouched.
3. Confirm there are no new fixed colors and no logic edits.
