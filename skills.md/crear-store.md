Crea un Pinia store llamado $ARGUMENTS.

Reglas obligatorias:
- JavaScript puro, sin TypeScript
- Patrón composition (función, no objeto de opciones)
- Archivo: $ARGUMENTS.js en `src/stores/`
- Exportar como `use[Nombre]Store`

Patrón base:
```js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'

export const use[Nombre]Store = defineStore('[nombre]', () => {
  // estado con ref()
  // derivados con computed()
  // acciones como funciones async con try/catch
  // llamadas HTTP con api, nunca axios directo

  return { /* solo lo necesario */ }
})
```

- Siempre `import api from '@/services/api'`, nunca `axios` directo
- Errores con `try/catch`, exponer un `error` ref si hay llamadas HTTP
- Deduce estado y acciones a partir del nombre: auth, events, badges, redemptions
