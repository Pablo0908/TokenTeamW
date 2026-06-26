---
name: create-store
description: Create a Pinia store for this project using the composition pattern. Use when the user needs shared state across screens (auth, events, badges) or asks to add a store/state module.
user-invocable: true
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
---

# /create-store — Create a Pinia Store

Create a Pinia store called `$ARGUMENTS` in `src/stores/$ARGUMENTS.js`.

## Mandatory rules

- **Composition (setup) pattern** — `defineStore('name', () => { ... })`, never the options object
- Plain JavaScript only
- All HTTP goes through the shared Axios instance: `import { api } from '@/services/api'`
  — never import `axios` directly
- Expose an `error` ref and a `loading` ref for any store that makes HTTP calls
- Map responses to plain JS objects; never drop raw Axios response objects into state
- Read API errors with `e.response?.data?.error ?? '<friendly fallback>'`
- Return every ref/computed/action you want exposed at the end

## Base structure

```js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/services/api'

const readError = (e) => e.response?.data?.error ?? 'Something went wrong.'

export const use$ARGUMENTSStore = defineStore('$ARGUMENTS', () => {
  const items = ref([])
  const error = ref(null)
  const loading = ref(false)

  async function fetchAll() {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.get('/...')
      items.value = data
    } catch (e) {
      error.value = readError(e)
    } finally {
      loading.value = false
    }
  }

  return { items, error, loading, fetchAll }
})
```
