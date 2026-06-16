# Diseño Técnico — Frontend
## Lyfter Badge App

> Documento interno del equipo de desarrollo.  
> Stack: Vue.js · Tailwind CSS · DaisyUI · Vue Router · Pinia · Axios

---

## Índice

1. [Tecnologías del Frontend](#1-tecnologías-del-frontend)
2. [Arquitectura de la app](#2-arquitectura-de-la-app)
3. [División de responsabilidades FE / BE](#3-división-de-responsabilidades-fe--be)
4. [Estructura de carpetas](#4-estructura-de-carpetas)
5. [Decisiones técnicas clave](#5-decisiones-técnicas-clave)

---

## 1. Tecnologías del Frontend

### Vue.js — El motor de la interfaz

Es el framework de JavaScript que usamos para construir todas las pantallas. Permite que la UI reaccione automáticamente a los cambios de datos sin recargar la página.

**Por qué encaja:** La app tiene pantallas que cambian según el estado del usuario (¿está logueado? ¿ya canjeó ese badge? ¿completó el evento?). Vue maneja esa reactividad de forma nativa.

**Ejemplo:** Cuando el usuario canjea un badge, la barra de progreso se actualiza en pantalla al instante, sin hacer refresh.

---

### Vue Router — La navegación entre pantallas

Librería oficial de Vue para manejar rutas. Permite que `/events` muestre la lista de eventos, `/profile` muestre el perfil, etc.

**Por qué es necesaria:** La app tiene pantallas para dos tipos de usuarios distintos (participante y admin). Vue Router permite proteger rutas: si alguien sin sesión intenta entrar a `/profile`, lo redirige automáticamente al login.

---

### Pinia — La memoria compartida de la app

Librería de Vue para manejar estado global, es decir, información que necesitan saber varias pantallas a la vez.

**Por qué es necesaria:** El JWT y los datos del usuario logueado los necesitan casi todas las pantallas. Pinia los guarda en un lugar central que cualquier componente puede consultar.

**Analogía:** Es como un pizarrón en la oficina que todos pueden leer y actualizar. Si el usuario hace login, Pinia guarda el token y cualquier pantalla que lo necesite lo consulta de ahí.

---

### Axios — El mensajero entre el Frontend y el Backend

Librería para hacer llamadas HTTP a la API de Flask.

**Por qué no usamos `fetch` directamente:** Axios permite configurar el token JWT una sola vez y lo incluye automáticamente en todos los requests siguientes. Sin eso, habría que escribirlo manualmente en cada llamada.

---

### Tailwind CSS — El sistema de estilos

Librería de CSS que funciona con clases utilitarias aplicadas directamente en el HTML. Permite construir interfaces rápido y de forma consistente, sin escribir archivos CSS desde cero.

---

### DaisyUI — Componentes visuales listos para usar

Capa sobre Tailwind que trae componentes completos: botones, tarjetas, barras de progreso, badges, modales, alerts. La app necesita todos estos elementos, DaisyUI los provee listos, con buen diseño.

---

## 2. Arquitectura de la app

### Pantallas (rutas)

La app tiene dos mundos separados: el del **participante** y el del **admin**.

```
PARTICIPANTE
├── /login                        → Formulario de inicio de sesión
├── /register                     → Formulario de registro
├── /events                       → Lista de eventos activos
├── /events/:id                   → Detalle de un evento con sus badges
├── /profile                      → Mi perfil: badges acumulados y progreso
└── /redeem/:eventId/:token       → Página pública de canje de QR

ADMIN
├── /admin/events                 → Lista de eventos creados
├── /admin/events/new             → Formulario para crear un nuevo evento
└── /admin/events/:id             → Detalle del evento: badges, QRs, participantes
```

---

### Componentes reutilizables

Un componente es un bloque visual que se construye una sola vez y se usa en múltiples pantallas.

| Componente | Qué hace | Dónde se usa |
|---|---|---|
| `BadgeCard` | Muestra un badge (obtenido o bloqueado) | Perfil, Detalle de evento |
| `ProgressBar` | Barra "X de Y badges completados" | Perfil, Detalle de evento |
| `EventCard` | Tarjeta con info resumida de un evento | Lista de eventos |
| `QRDisplay` | Muestra la imagen del QR y botón de descarga | Panel admin |
| `NavBar` | Barra de navegación superior | Todas las pantallas autenticadas |
| `AlertMessage` | Mensaje de éxito o error | Canje, login, formularios |
| `LoadingSpinner` | Animación de carga mientras se espera la API | Cualquier pantalla con fetch |

---

### Flujo de navegación — Participante (escaneo de QR)

```
Usuario escanea el QR
         │
         ▼
/redeem/:eventId/:token
         │
   ¿Tiene sesión activa?
    /            \
  SÍ              NO
   │               │
   ▼               ▼
Registra       /login → /register
el badge            │
   │                │ (después de autenticarse)
   │                ▼
   └──────► Completa el canje
                    │
                    ▼
          Feedback visual:
          badge obtenido ✓
          o evento completado + premio 🎉
```

### Flujo de navegación — Admin (creación de evento)

```
Admin inicia sesión
         │
         ▼
/admin/events  →  /admin/events/new
         │                │
         │          Completa formulario
         │                │
         ▼                ▼
/admin/events/:id  ←  (redirige al detalle)
         │
   Agrega badges
         │
         ▼
Muestra QR generado + botón de descarga
```

---

## 3. División de responsabilidades FE / BE

> **Analogía:** El Frontend es el mozo, el Backend es la cocina. El mozo toma el pedido, lo lleva a la cocina, y trae el resultado al cliente. Nunca cocina él mismo.

---

### Qué hace el Frontend (sin pedirle nada al Backend)

- Mostrar pantallas, formularios y botones
- Validar que los campos no estén vacíos antes de enviar
- Guardar el JWT en `localStorage` después del login
- Incluir el JWT automáticamente en todos los requests (vía Axios)
- Calcular visualmente la barra de progreso con datos ya recibidos
- Redirigir al usuario si intenta acceder a una ruta no permitida
- Mostrar estados de carga mientras espera respuesta del backend
- Mostrar mensajes de éxito o error según la respuesta recibida

---

### Qué le pide al Backend (llamadas a la API)

#### Autenticación

**Registrar un usuario nuevo**
```
POST /auth/register
Body: { nombre: "Ana García", email: "ana@mail.com", password: "1234" }
Respuesta: { message: "Usuario creado", user_id: "abc123" }
```

**Iniciar sesión**
```
POST /auth/login
Body: { email: "ana@mail.com", password: "1234" }
Respuesta: { token: "eyJhbGci...", role: "participant" }
→ El frontend guarda el token y redirige según el rol
```

---

#### Flujo del participante

**Ver la lista de eventos**
```
GET /events/
Headers: { Authorization: "Bearer eyJhbGci..." }
Respuesta: [
  { id: "ev1", nombre: "Lyftercon 2025", fecha: "2025-09-10" },
  ...
]
```

**Ver el detalle de un evento**
```
GET /events/ev1
Headers: { Authorization: "Bearer eyJhbGci..." }
Respuesta: {
  nombre: "Lyftercon 2025",
  badges: [
    { id: "b1", nombre: "Apertura", obtenido: true },
    { id: "b2", nombre: "Workshop Vue", obtenido: false }
  ],
  premio: "Acceso VIP al próximo evento"
}
```

**Ver mi perfil con todos mis badges**
```
GET /me/badges
Headers: { Authorization: "Bearer eyJhbGci..." }
Respuesta: [
  {
    evento: "Lyftercon 2025",
    badges_obtenidos: 3,
    badges_totales: 8,
    completado: false,
    badges: [
      { nombre: "Apertura", fecha_canje: "2025-09-10" },
      ...
    ]
  }
]
```

**Canjear un badge (URL del QR)**
```
GET /redeem/ev1/token-uuid-generado
Headers: { Authorization: "Bearer eyJhbGci..." }

Respuesta — badge canjeado:
  { message: "Badge canjeado", evento_completado: false }

Respuesta — evento completado:
  { message: "¡Evento completado!", premio: "Acceso VIP..." }

Respuesta — error:
  { message: "Este badge ya fue canjeado" }
```

---

#### Flujo del admin

**Crear un evento**
```
POST /admin/event
Headers: { Authorization: "Bearer eyJhbGci..." }
Body: {
  nombre: "Lyftercon 2025",
  descripcion: "Evento anual de Lyfter",
  fecha_inicio: "2025-09-10",
  premio: "Acceso VIP"
}
Respuesta: { id: "ev1", nombre: "Lyftercon 2025" }
```

**Agregar un badge a un evento**
```
POST /admin/events/ev1/badge
Headers: { Authorization: "Bearer eyJhbGci..." }
Body: { nombre: "Charla de Apertura", descripcion: "Keynote principal" }
Respuesta: { id: "b1", token: "uuid-generado", qr_url: "https://..." }
→ El frontend muestra el QR en pantalla y habilita el botón de descarga
```

**Ver todos los badges de un evento**
```
GET /admin/events/ev1/badges
Headers: { Authorization: "Bearer eyJhbGci..." }
Respuesta: [
  { nombre: "Apertura", canjeado_por: 42, total_asistentes: 60 },
  { nombre: "Workshop Vue", canjeado_por: 28, total_asistentes: 60 }
]
```

---

## 4. Estructura de carpetas

```
frontend/
├── public/                      # Archivos estáticos (favicon, etc.)
│
├── src/
│   ├── assets/                  # Imágenes, íconos, logo de Lyfter
│   │
│   ├── components/              # Bloques visuales reutilizables
│   │   ├── BadgeCard.vue
│   │   ├── ProgressBar.vue
│   │   ├── EventCard.vue
│   │   ├── QRDisplay.vue
│   │   ├── NavBar.vue
│   │   ├── AlertMessage.vue
│   │   └── LoadingSpinner.vue
│   │
│   ├── pages/                   # Pantallas completas de la app
│   │   ├── LoginPage.vue
│   │   ├── RegisterPage.vue
│   │   ├── EventsPage.vue
│   │   ├── EventDetailPage.vue
│   │   ├── ProfilePage.vue
│   │   ├── RedeemPage.vue
│   │   └── admin/
│   │       ├── AdminEventsPage.vue
│   │       ├── AdminNewEventPage.vue
│   │       └── AdminEventDetailPage.vue
│   │
│   ├── router/                  # Configuración de navegación
│   │   └── index.js             # Define qué URL muestra qué pantalla + guards
│   │
│   ├── stores/                  # Estado global (Pinia)
│   │   ├── auth.js              # Token JWT y datos del usuario logueado
│   │   └── events.js            # Eventos y badges cargados
│   │
│   ├── services/                # Funciones para llamar a la API
│   │   ├── api.js               # Configuración base de Axios (URL base, token)
│   │   ├── authService.js       # login(), register()
│   │   ├── eventsService.js     # getEvents(), getEvent(), createEvent()
│   │   └── badgesService.js     # getMyBadges(), redeemBadge(), addBadge()
│   │
│   ├── App.vue                  # Componente raíz
│   └── main.js                  # Punto de entrada: arranca la app
│
├── .env                         # Variables de entorno (URL del backend)
├── index.html
└── package.json                 # Dependencias del proyecto
```

### Regla simple para saber dónde va cada archivo

| Pregunta | Carpeta |
|---|---|
| ¿Es una pantalla completa con su propia URL? | `pages/` |
| ¿Es un bloque visual que se usa en varias pantallas? | `components/` |
| ¿Hace una llamada a la API? | `services/` |
| ¿Guarda información que necesitan varias pantallas? | `stores/` |
| ¿Configura qué URL muestra qué pantalla? | `router/` |

---

## 5. Decisiones técnicas clave

### Separar `pages/` de `components/`

**Qué significa:** Las pantallas completas van en una carpeta, los bloques reutilizables en otra.

**Por qué:** Con 10 archivos todo es fácil de encontrar. Con 40, esta separación es la diferencia entre encontrar algo en 10 segundos o perderse. También permite que distintos miembros del equipo trabajen en paralelo sin pisarse.

---

### Toda comunicación con el backend pasa por `services/`

**Qué significa:** Ninguna pantalla llama a la API directamente. Siempre llama a una función de `services/`.

**Por qué:** Si el backend cambia una URL (de `/events` a `/api/events`), el cambio se hace en un solo lugar, no en 5 pantallas distintas.

---

### El JWT se guarda en `localStorage` y se envía automáticamente con Axios

**Qué significa:** Al hacer login, el frontend guarda el token en el navegador. Axios está configurado para incluirlo en todos los requests siguientes de forma automática.

**Por qué:** Las pantallas solo llaman a la función del servicio y no necesitan saber nada sobre autenticación. Simplifica el código considerablemente.

---

### Las rutas protegidas se verifican con Navigation Guards de Vue Router

**Qué significa:** Antes de mostrar cada pantalla, Vue Router verifica si el usuario tiene permiso de estar ahí.

**Por qué:** Sin guards, cualquier persona podría escribir `/admin/events` en la URL y ver el panel de admin aunque no lo sea.

**Reglas de acceso:**

| Ruta | Acceso |
|---|---|
| `/login`, `/register` | Público |
| `/redeem/:eventId/:token` | Público (ver decisión siguiente) |
| `/events`, `/profile` | Requiere estar logueado |
| `/admin/*` | Requiere estar logueado + `role: "admin"` |

---

### La página `/redeem` es pública pero guarda el destino

**Qué significa:** El QR lleva a una URL que cualquier persona puede abrir sin estar logueada.

**Por qué:** El flujo real es: el asistente llega a la sala, escanea el QR, la app lo recibe. Si esa URL requiriera login de entrada, los usuarios nuevos nunca completarían el canje.

**Cómo funciona:**
1. El usuario llega a `/redeem/:eventId/:token` sin sesión
2. El router guarda la URL en `localStorage` como `redirectAfterLogin`
3. Redirige al login (o registro)
4. Después del login, el router lee `redirectAfterLogin` y lleva al usuario de vuelta al canje automáticamente