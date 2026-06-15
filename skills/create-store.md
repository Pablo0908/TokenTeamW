Create a Pinia store called $ARGUMENTS.

Mandatory rules:
- Plain JavaScript, no TypeScript
- Composition pattern (function, not options object)
- File: $ARGUMENTS.js in `src/stores/`
- Export as `use[Name]Store`

Base pattern:
js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'

export const use[Name]Store = defineStore('[name]', () => {
  // state with ref()
  // derived values with computed()
  // actions as async functions with try/catch
  // HTTP calls with api, never axios directly

  return { /* only what's needed */ }
})

- Always `import api from '@/services/api'`, never `axios` directly
- Errors with `try/catch`, expose an `error` ref if there are HTTP calls
- Infer state and actions from the name: auth, events, badges, redemptions
