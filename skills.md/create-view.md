Crea una vista Vue 3 llamada $ARGUMENTS.

Reglas obligatorias:
- `<script setup>` con JavaScript puro, sin TypeScript
- Archivo: $ARGUMENTSView.vue en `src/views/`
- Si requiere auth, agregar meta `requiresAuth: true` en comentario superior
- Si es solo para admin, agregar meta `requiresAdmin: true`

Layout:
- Fondo: `min-h-screen bg-base-300` o `bg-app-gradient`
- Contenedor móvil: `max-w-md mx-auto px-4 py-6`
- DaisyUI para todos los elementos: `card`, `btn`, `input`, `badge`, `alert`
- Tailwind para espaciado y estructura
- Mobile-first obligatorio

Imports a incluir según el propósito de la vista:
- `import { useRouter } from 'vue-router'`
- `import { useAuthStore } from '@/stores/auth'`
- `import api from '@/services/api'`

Errores de API: siempre mostrar `err.response?.data?.error ?? 'Error inesperado'`

Deduce el contenido a partir del nombre: Login, Home, Events, Badges, Scanner, Admin, etc.
