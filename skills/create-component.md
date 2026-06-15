Create a Vue 3 component called $ARGUMENTS.

Mandatory rules:
- `<script setup>` with plain JavaScript, no TypeScript
- File in PascalCase: $ARGUMENTS.vue
- Location: `src/components/ui/` if generic, `src/components/domain/` if business-specific
- Props with `defineProps`, emits with `defineEmits`

Styles:
- DaisyUI first: `btn`, `card`, `badge`, `input`, `alert` as appropriate
- Tailwind for layout and spacing: `flex`, `gap-4`, `p-4`, etc.
- Dark theme colors: `bg-base-100`, `bg-base-200`, `text-base-content`
- Do not use fixed colors like `bg-blue-500` if DaisyUI already covers them
- Mobile-first: design for mobile first, then `sm:` and `md:` for larger screens

Base structure:
vue
<script setup>
import { ref } from 'vue'

const props = defineProps({
  // props based on context
})

const emit = defineEmits([/* events based on context */])
</script>

<template>
  <!-- DaisyUI + Tailwind, dark theme -->
</template>

<style scoped>
/* only if Tailwind/DaisyUI is not enough */
</style>


Infer props and emits from the component name and project context: badges, events, QR, users, admin/assistant roles.