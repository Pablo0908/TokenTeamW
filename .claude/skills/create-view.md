---
name: create-view
description: Create a route-level Vue 3 view for this project, wired into the router with the right auth meta. Use when the user asks for a new screen/page reachable by a URL.
user-invocable: true
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
---

# /create-view — Create a Route-Level View

Create a view called `$ARGUMENTS` in `src/views/` (or `src/views/admin/` for organizer screens).

## Mandatory rules

- `<script setup>`, plain JavaScript, mobile-first
- Views are **thin**: fetch through a Pinia store, render the result. No direct `axios`
- Handle the three states explicitly: **loading**, **error** (via `AlertMessage`), **empty**
- Base container is centered and mobile-first (the app shell already applies `max-w-md mx-auto`);
  use `px-4` and top padding inside the view
- Register the route in `src/router/index.js` with the correct `meta`:
  - public: `meta: { public: true }`
  - signed-in attendee: `meta: { requiresAuth: true }`
  - organizer: `meta: { requiresAuth: true, requiresAdmin: true }`
- Use lazy import in the router: `component: () => import('@/views/$ARGUMENTS.vue')`

## Base structure

```vue
<script setup>
import { onMounted } from 'vue'
import { useSomeStore } from '@/stores/some'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import AlertMessage from '@/components/ui/AlertMessage.vue'

const store = useSomeStore()
onMounted(() => store.fetchAll())
</script>

<template>
  <div class="space-y-5 px-4 pb-4 pt-6">
    <AlertMessage type="warning" :message="store.error || ''" />
    <LoadingSpinner v-if="store.loading" />
    <!-- content -->
  </div>
</template>
```
