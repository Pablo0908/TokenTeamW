Crea un componente Vue 3 llamado $ARGUMENTS.

Reglas obligatorias:
- `<script setup>` con JavaScript puro, sin TypeScript
- Archivo en PascalCase: $ARGUMENTS.vue
- Ubicación: `src/components/ui/` si es genérico, `src/components/domain/` si es de negocio
- Props con `defineProps`, emits con `defineEmits`

Estilos:
- DaisyUI primero: `btn`, `card`, `badge`, `input`, `alert` según corresponda
- Tailwind para layout y espaciado: `flex`, `gap-4`, `p-4`, etc.
- Colores del tema oscuro: `bg-base-100`, `bg-base-200`, `text-base-content`
- No usar colores fijos como `bg-blue-500` si DaisyUI ya los cubre
- Mobile-first: diseñar para celular primero, luego `sm:` y `md:` para pantallas grandes

Estructura base:
```vue
<script setup>
import { ref } from 'vue'

const props = defineProps({
  // props según el contexto
})

const emit = defineEmits([/* eventos según el contexto */])
</script>

<template>
  <!-- DaisyUI + Tailwind, tema oscuro -->
</template>

<style scoped>
/* solo si Tailwind/DaisyUI no alcanza */
</style>
```

Deduce props y emits a partir del nombre del componente y el contexto del proyecto: badges, eventos, QR, usuarios, roles admin/asistente.
