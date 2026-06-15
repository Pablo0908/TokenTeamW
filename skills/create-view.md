markdown
Create a Vue 3 view called $ARGUMENTS.

Mandatory rules:
- `<script setup>` with plain JavaScript, no TypeScript
- File: $ARGUMENTSView.vue in `src/views/`
- If auth is required, add meta `requiresAuth: true` in a top comment
- If admin-only, add meta `requiresAdmin: true`

Layout:
- Background: `min-h-screen bg-base-300` or `bg-app-gradient`
- Mobile container: `max-w-md mx-auto px-4 py-6`
- DaisyUI for all elements: `card`, `btn`, `input`, `badge`, `alert`
- Tailwind for spacing and structure
- Mobile-first mandatory

Imports to include based on the view's purpose:
- `import { useRouter } from 'vue-router'`
- `import { useAuthStore } from '@/stores/auth'`
- `import api from '@/services/api'`

API errors: always display `err.response?.data?.error ?? 'Unexpected error'`

Infer content from the name: Login, Home, Events, Badges, Scanner, Admin, etc.