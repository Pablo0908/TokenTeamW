Dale estilo al componente Vue pegado a continuación usando Tailwind CSS + DaisyUI.

$ARGUMENTS

Reglas:
- NO cambiar lógica, props, emits ni datos reactivos — solo clases
- Jerarquía: DaisyUI primero → Tailwind para ajustes → CSS custom solo si no hay otra opción
- Tema oscuro: `bg-base-100`, `bg-base-200`, `bg-base-300`, `text-base-content`
- Botones: `btn btn-primary`, `btn btn-secondary`, `btn btn-error btn-sm`
- Tarjetas: `card bg-base-100 shadow-xl`
- Inputs: `input input-bordered bg-neutral w-full`
- Estado activo: `badge badge-success`
- Estado próximo: `badge badge-secondary`
- Estado pasado: `badge badge-ghost opacity-50`
- Mobile-first: que se vea bien en celular primero
- No usar colores fijos si DaisyUI ya los cubre

Devuelve solo el componente completo con los estilos aplicados.
