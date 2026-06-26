---
name: create-component
description: Create a Vue 3 component for this project. Use when the user asks to create a component, add a UI element, or needs a reusable piece of the interface such as a badge card, event card, or QR scanner.
user-invocable: true
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
---

# /create-component — Create a Vue 3 Component

Create a Vue 3 component called `$ARGUMENTS`.

## Mandatory rules

- `<script setup>` with plain JavaScript — no TypeScript, no Options API
- File in PascalCase: `$ARGUMENTS.vue`
- Location: `src/components/ui/` if generic (NavBar, AlertMessage, LoadingSpinner),
  `src/components/domain/` if business-specific (BadgeCard, EventCard, ProgressBar, QRDisplay)
- Props with `defineProps`, events with `defineEmits` — never mutate props
- Keep it under ~150 lines; one responsibility per component
- Receive data via props; do not fetch the API from a component (views/stores do that)

## Styles (mobile-first)

- DaisyUI first: `btn`, `card`, `badge`, `input`, `alert`, `progress`, `modal`
- Tailwind for layout/spacing: `flex`, `gap-4`, `p-4`, `max-w-md`
- Dark theme tokens only: `bg-base-100/200/300`, `text-base-content`, semantic
  `primary`/`secondary`/`accent`/`success`/`info`/`warning`/`error`
- Never hardcode colors like `bg-blue-500` where a DaisyUI token exists
- Tap targets ≥ 44×44 px — add the `tap-target` utility on interactive elements
- When mapping a dynamic color to a class, use a static lookup object (full class
  strings) so Tailwind's purge keeps them

## Base structure

```vue
<script setup>
import { computed } from 'vue'

const props = defineProps({
  // ...
})
defineEmits(['select'])
</script>

<template>
  <!-- mobile-first markup -->
</template>
```
