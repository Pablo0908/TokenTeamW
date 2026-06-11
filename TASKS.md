# TASKS — Lyfter Badge System
> **Proyecto:** TokenTeamW · **Empresa:** Lyfter · **Evento:** Costa Rica, Noviembre 2026
> **Equipo:** 5 integrantes · **Duración:** 3 semanas · **Idioma:** Español

---

## Stack Tecnológico

| Capa | Tecnología |
|---|---|
| Frontend | Next.js 14 (App Router) + Tailwind CSS + shadcn/ui |
| Backend | Node.js + Express |
| Base de datos | MongoDB Atlas + Mongoose |
| Autenticación | JWT + bcrypt |
| Generación QR | `qrcode` (npm) |
| Escaneo QR | `react-qr-reader` o Web API de cámara |
| Tiempo real | Socket.io |
| Imágenes badge | `html2canvas` + Web Share API |
| Deploy Frontend | Vercel |
| Deploy Backend | Railway |

---

## Estructura de Carpetas

```
TokenTeamW/
├── client/                  # Next.js frontend
│   ├── app/
│   │   ├── (auth)/
│   │   │   └── login/
│   │   ├── (dashboard)/
│   │   │   ├── admin/
│   │   │   ├── eventos/
│   │   │   └── estadisticas/
│   │   ├── escanear/
│   │   ├── mis-badges/
│   │   └── historial/
│   ├── components/
│   ├── context/
│   ├── hooks/
│   └── lib/
├── server/                  # Express backend
│   ├── config/
│   ├── controllers/
│   ├── middleware/
│   ├── models/
│   ├── routes/
│   ├── services/
│   └── utils/
└── TASKS.md
```

---

## Schemas de MongoDB (Modelos de la App)

### Colección: `usuarios`
```json
{
  "_id": "ObjectId",
  "nombre": "String",
  "email": "String (único)",
  "contraseña": "String (hash bcrypt)",
  "rol": "String (enum: ['admin', 'asistente'])",
  "badges_ganados": ["ObjectId → Badge"],
  "activo": "Boolean (default: true)",
  "createdAt": "Date",
  "updatedAt": "Date"
}
```

### Colección: `eventos`
```json
{
  "_id": "ObjectId",
  "nombre": "String",
  "descripcion": "String",
  "fecha": "Date",
  "lugar": "String",
  "capacidad_maxima": "Number",
  "organizador": "ObjectId → Usuario",
  "estado": "String (enum: ['borrador', 'activo', 'finalizado'])",
  "imagen_portada": "String (URL)",
  "createdAt": "Date",
  "updatedAt": "Date"
}
```

### Colección: `badges`
```json
{
  "_id": "ObjectId",
  "nombre": "String",
  "descripcion": "String",
  "evento": "ObjectId → Evento",
  "imagen_url": "String",
  "qr_token": "String (UUID único, indexado)",
  "qr_imagen_url": "String (data URL o S3)",
  "limite_redencion": "Number (null = ilimitado)",
  "total_redimidos": "Number (default: 0)",
  "activo": "Boolean (default: true)",
  "createdAt": "Date",
  "updatedAt": "Date"
}
```

### Colección: `redenciones`
```json
{
  "_id": "ObjectId",
  "badge": "ObjectId → Badge",
  "evento": "ObjectId → Evento",
  "usuario": "ObjectId → Usuario",
  "qr_token_usado": "String",
  "fecha_redencion": "Date",
  "metadata": {
    "user_agent": "String",
    "ip": "String"
  }
}
```

---

## Schema de la Colección `tasks` (este archivo en MongoDB)

```json
{
  "_id": "ObjectId",
  "codigo": "String",
  "titulo": "String",
  "descripcion": "String",
  "modulo": "String (enum: ['setup','auth','eventos','qr','badges','frontend','stats','realtime','historial','share','deploy'])",
  "sprint": "Number (1 | 2 | 3)",
  "prioridad": "String (enum: ['critica','alta','media','baja'])",
  "estado": "String (enum: ['pendiente','en_progreso','revision','completado'])",
  "horas_estimadas": "Number",
  "asignado_a": "String (null por defecto)",
  "dependencias": ["String (codigos de tasks previas)"],
  "criterios_aceptacion": ["String"]
}
```

---

## SPRINT 1 — Semana 1: Fundación y Arquitectura
> **Objetivo:** Repositorio listo, base de datos conectada, modelos definidos y autenticación funcional de punta a punta.

---

### Módulo: `setup`

```json
{
  "codigo": "SETUP-001",
  "titulo": "Inicializar estructura del monorepo",
  "descripcion": "Crear el repositorio con las carpetas /client (Next.js) y /server (Express). Configurar .gitignore, README base y ESLint compartido. Instalar dependencias iniciales de ambos lados.",
  "modulo": "setup",
  "sprint": 1,
  "prioridad": "critica",
  "estado": "pendiente",
  "horas_estimadas": 3,
  "asignado_a": null,
  "dependencias": [],
  "criterios_aceptacion": [
    "Carpeta /client con Next.js 14 corriendo en localhost:3000",
    "Carpeta /server con Express corriendo en localhost:5000",
    "Ambos proyectos tienen su propio package.json",
    ".gitignore excluye node_modules y .env"
  ]
}
```

```json
{
  "codigo": "SETUP-002",
  "titulo": "Configurar MongoDB Atlas y conexión Mongoose",
  "descripcion": "Crear cluster en MongoDB Atlas (free tier). Crear usuario de base de datos con permisos de lectura/escritura. Configurar IP Whitelist para desarrollo (0.0.0.0/0). Crear archivo db.js en /server/config con la lógica de conexión y manejo de errores.",
  "modulo": "setup",
  "sprint": 1,
  "prioridad": "critica",
  "estado": "pendiente",
  "horas_estimadas": 2,
  "asignado_a": null,
  "dependencias": ["SETUP-001"],
  "criterios_aceptacion": [
    "Cluster creado en MongoDB Atlas",
    "Conexión exitosa desde el servidor local",
    "Log 'MongoDB conectado' al iniciar el servidor",
    "Manejo de error si la conexión falla (proceso no se rompe silenciosamente)"
  ]
}
```

```json
{
  "codigo": "SETUP-003",
  "titulo": "Configurar variables de entorno",
  "descripcion": "Crear archivos .env para /server y /client. Documentar todas las variables necesarias en un .env.example que sí se sube al repositorio. Variables: MONGODB_URI, JWT_SECRET, JWT_EXPIRES_IN, PORT, CLIENT_URL, NODE_ENV.",
  "modulo": "setup",
  "sprint": 1,
  "prioridad": "critica",
  "estado": "pendiente",
  "horas_estimadas": 1,
  "asignado_a": null,
  "dependencias": ["SETUP-001"],
  "criterios_aceptacion": [
    "Archivo .env existe y no está en git",
    "Archivo .env.example está en git con todas las variables sin valores reales",
    "El servidor lee las variables correctamente con dotenv",
    "JWT_SECRET tiene al menos 32 caracteres aleatorios"
  ]
}
```

```json
{
  "codigo": "SETUP-004",
  "titulo": "Definir todos los modelos Mongoose",
  "descripcion": "Crear los 4 modelos principales en /server/models: Usuario.js, Evento.js, Badge.js, Redencion.js. Aplicar los schemas definidos en este documento. Agregar timestamps: true a todos los schemas. Crear índices únicos donde corresponda (email en Usuario, qr_token en Badge).",
  "modulo": "setup",
  "sprint": 1,
  "prioridad": "critica",
  "estado": "pendiente",
  "horas_estimadas": 4,
  "asignado_a": null,
  "dependencias": ["SETUP-002", "SETUP-003"],
  "criterios_aceptacion": [
    "Los 4 modelos existen en /server/models",
    "Cada modelo valida los campos requeridos (required: true)",
    "Índice único en Usuario.email",
    "Índice único en Badge.qr_token",
    "Relaciones con ObjectId y ref correctamente definidas"
  ]
}
```

```json
{
  "codigo": "SETUP-005",
  "titulo": "Configurar middleware base del servidor Express",
  "descripcion": "Configurar en server.js: CORS con lista de orígenes permitidos (localhost:3000 en dev, URL de Vercel en prod), express.json(), express.urlencoded(), morgan para logs de requests, y el handler de errores global. Estructura de rutas con prefijo /api.",
  "modulo": "setup",
  "sprint": 1,
  "prioridad": "alta",
  "estado": "pendiente",
  "horas_estimadas": 2,
  "asignado_a": null,
  "dependencias": ["SETUP-001"],
  "criterios_aceptacion": [
    "GET /api/health retorna { status: 'ok' }",
    "CORS permite requests desde localhost:3000",
    "Errores no controlados retornan JSON (no HTML)",
    "Logs de requests visibles en consola durante desarrollo"
  ]
}
```

---

### Módulo: `auth`

```json
{
  "codigo": "AUTH-001",
  "titulo": "Endpoint: Registro de administrador",
  "descripcion": "POST /api/auth/registro — Crear un nuevo usuario con rol 'admin'. Validar que el email no exista. Hashear la contraseña con bcrypt (saltRounds: 12). Retornar JWT firmado. Este endpoint puede requerir una clave secreta de admin para no ser público.",
  "modulo": "auth",
  "sprint": 1,
  "prioridad": "critica",
  "estado": "pendiente",
  "horas_estimadas": 3,
  "asignado_a": null,
  "dependencias": ["SETUP-004", "SETUP-005"],
  "criterios_aceptacion": [
    "Retorna 201 con token JWT al registrar exitosamente",
    "Retorna 409 si el email ya existe",
    "La contraseña nunca se devuelve en la respuesta",
    "El hash en MongoDB no es texto plano"
  ]
}
```

```json
{
  "codigo": "AUTH-002",
  "titulo": "Endpoint: Login de usuario (admin y asistente)",
  "descripcion": "POST /api/auth/login — Recibir email y contraseña. Buscar usuario por email. Comparar contraseña con bcrypt.compare. Si es válido, retornar JWT con payload { userId, email, rol }. Manejar errores de credenciales inválidas sin revelar si el email existe o no.",
  "modulo": "auth",
  "sprint": 1,
  "prioridad": "critica",
  "estado": "pendiente",
  "horas_estimadas": 3,
  "asignado_a": null,
  "dependencias": ["AUTH-001"],
  "criterios_aceptacion": [
    "Retorna 200 con { token, usuario: { id, nombre, email, rol } }",
    "Retorna 401 con mensaje genérico para credenciales inválidas",
    "Token JWT expira según JWT_EXPIRES_IN del .env",
    "El rol está incluido en el payload del token"
  ]
}
```

```json
{
  "codigo": "AUTH-003",
  "titulo": "Middleware: Verificación de JWT",
  "descripcion": "Crear middleware verificarToken en /server/middleware/auth.js. Extraer token del header Authorization (Bearer). Verificar firma con jwt.verify. Adjuntar datos del usuario a req.usuario. Retornar 401 si el token falta o es inválido.",
  "modulo": "auth",
  "sprint": 1,
  "prioridad": "critica",
  "estado": "pendiente",
  "horas_estimadas": 2,
  "asignado_a": null,
  "dependencias": ["AUTH-002"],
  "criterios_aceptacion": [
    "Rutas protegidas retornan 401 sin token",
    "Rutas protegidas retornan 401 con token expirado",
    "req.usuario contiene { id, email, rol } en rutas autenticadas",
    "Token malformado retorna 401 (no 500)"
  ]
}
```

```json
{
  "codigo": "AUTH-004",
  "titulo": "Middleware: Autorización por rol",
  "descripcion": "Crear middleware requireRol(...roles) que verifica si el usuario autenticado tiene uno de los roles permitidos. Retornar 403 si no tiene permisos. Usar en conjunto con verificarToken.",
  "modulo": "auth",
  "sprint": 1,
  "prioridad": "alta",
  "estado": "pendiente",
  "horas_estimadas": 1,
  "asignado_a": null,
  "dependencias": ["AUTH-003"],
  "criterios_aceptacion": [
    "requireRol('admin') bloquea asistentes con 403",
    "requireRol('admin', 'asistente') permite ambos roles",
    "Mensaje de error claro: 'No tienes permisos para esta acción'"
  ]
}
```

```json
{
  "codigo": "AUTH-005",
  "titulo": "Endpoint: Registro de asistente",
  "descripcion": "POST /api/auth/registro-asistente — Igual que AUTH-001 pero crea usuario con rol 'asistente'. Este endpoint es público para que los asistentes puedan registrarse antes del evento. Validar formato de email y contraseña mínima de 8 caracteres.",
  "modulo": "auth",
  "sprint": 1,
  "prioridad": "alta",
  "estado": "pendiente",
  "horas_estimadas": 2,
  "asignado_a": null,
  "dependencias": ["SETUP-004"],
  "criterios_aceptacion": [
    "Retorna 201 con token y datos del usuario asistente",
    "Contraseña con menos de 8 caracteres retorna 400",
    "Email inválido retorna 400 con mensaje descriptivo",
    "No permite crear usuarios con rol 'admin' desde este endpoint"
  ]
}
```

```json
{
  "codigo": "AUTH-006",
  "titulo": "Frontend: Pantalla de login",
  "descripcion": "Crear página /login en Next.js con formulario de email y contraseña. Al hacer submit, llamar al endpoint de login. Guardar el token en localStorage o cookie httpOnly. Redirigir al dashboard según el rol del usuario. Mostrar feedback de error si las credenciales son incorrectas.",
  "modulo": "auth",
  "sprint": 1,
  "prioridad": "critica",
  "estado": "pendiente",
  "horas_estimadas": 4,
  "asignado_a": null,
  "dependencias": ["AUTH-002"],
  "criterios_aceptacion": [
    "Formulario con validación en cliente (campos vacíos)",
    "Spinner visible durante el request",
    "Admin redirige a /admin/dashboard",
    "Asistente redirige a /mis-badges",
    "Mensaje de error visible si login falla"
  ]
}
```

```json
{
  "codigo": "AUTH-007",
  "titulo": "Frontend: Contexto global de autenticación",
  "descripcion": "Crear AuthContext con React Context API. Exponer: { usuario, token, login, logout, cargando }. Persistir sesión en localStorage. Crear hook useAuth() para acceder al contexto. Implementar rutas protegidas que redirijan a /login si no hay sesión activa.",
  "modulo": "auth",
  "sprint": 1,
  "prioridad": "critica",
  "estado": "pendiente",
  "horas_estimadas": 4,
  "asignado_a": null,
  "dependencias": ["AUTH-006"],
  "criterios_aceptacion": [
    "Al recargar la página, la sesión persiste",
    "logout() elimina el token y redirige a /login",
    "Componente ProtectedRoute redirige si no hay token",
    "El rol del usuario es accesible desde cualquier componente"
  ]
}
```

---

## SPRINT 2 — Semana 2: Core Features
> **Objetivo:** Flujo completo de creación de evento → generación de QR → escaneo → redención de badge funcionando.

---

### Módulo: `eventos`

```json
{
  "codigo": "EVENTO-001",
  "titulo": "Endpoint: Crear evento",
  "descripcion": "POST /api/eventos — Solo admin. Recibir nombre, descripción, fecha, lugar, capacidad_maxima, imagen_portada. Asignar organizador desde req.usuario.id. Estado inicial: 'borrador'. Validar que la fecha sea futura.",
  "modulo": "eventos",
  "sprint": 2,
  "prioridad": "critica",
  "estado": "pendiente",
  "horas_estimadas": 3,
  "asignado_a": null,
  "dependencias": ["AUTH-004", "SETUP-004"],
  "criterios_aceptacion": [
    "Retorna 201 con el evento creado",
    "Solo accesible con token de admin",
    "Fecha en el pasado retorna 400",
    "Campos requeridos faltantes retornan 400 con detalle por campo"
  ]
}
```

```json
{
  "codigo": "EVENTO-002",
  "titulo": "Endpoint: Listar eventos",
  "descripcion": "GET /api/eventos — Público. Retornar lista de eventos activos y borradores. Incluir paginación (página, límite). Soportar query ?estado=activo|finalizado|borrador para filtrar. Popular campo organizador con nombre y email.",
  "modulo": "eventos",
  "sprint": 2,
  "prioridad": "critica",
  "estado": "pendiente",
  "horas_estimadas": 2,
  "asignado_a": null,
  "dependencias": ["EVENTO-001"],
  "criterios_aceptacion": [
    "Retorna array de eventos con paginación ({ data, pagina, total, paginas })",
    "Filtro por estado funciona correctamente",
    "Organizador muestra nombre y email (no contraseña)"
  ]
}
```

```json
{
  "codigo": "EVENTO-003",
  "titulo": "Endpoint: Detalle de evento",
  "descripcion": "GET /api/eventos/:id — Público. Retornar el evento con sus badges asociados (populate). Retornar 404 si no existe.",
  "modulo": "eventos",
  "sprint": 2,
  "prioridad": "alta",
  "estado": "pendiente",
  "horas_estimadas": 1,
  "asignado_a": null,
  "dependencias": ["EVENTO-002"],
  "criterios_aceptacion": [
    "Retorna el evento con array de badges asociados",
    "Retorna 404 si el ID no existe o es inválido",
    "ID malformado retorna 400 (no 500)"
  ]
}
```

```json
{
  "codigo": "EVENTO-004",
  "titulo": "Endpoint: Editar evento",
  "descripcion": "PUT /api/eventos/:id — Solo admin. Permitir actualizar cualquier campo del evento. Validar que el organizador del evento sea el admin autenticado (o que sea superadmin). Actualizar updatedAt automáticamente.",
  "modulo": "eventos",
  "sprint": 2,
  "prioridad": "alta",
  "estado": "pendiente",
  "horas_estimadas": 2,
  "asignado_a": null,
  "dependencias": ["EVENTO-001", "AUTH-004"],
  "criterios_aceptacion": [
    "Retorna 200 con el evento actualizado",
    "Retorna 403 si el admin no es el organizador",
    "Retorna 404 si el evento no existe"
  ]
}
```

```json
{
  "codigo": "EVENTO-005",
  "titulo": "Endpoint: Cambiar estado de evento",
  "descripcion": "PATCH /api/eventos/:id/estado — Solo admin. Cambiar el estado del evento entre borrador → activo → finalizado. Un evento finalizado no puede volver a activo.",
  "modulo": "eventos",
  "sprint": 2,
  "prioridad": "alta",
  "estado": "pendiente",
  "horas_estimadas": 2,
  "asignado_a": null,
  "dependencias": ["EVENTO-004"],
  "criterios_aceptacion": [
    "Retorna 200 con el evento en el nuevo estado",
    "Transición inválida (ej: finalizado → activo) retorna 400",
    "Solo el organizador puede cambiar el estado"
  ]
}
```

```json
{
  "codigo": "EVENTO-006",
  "titulo": "Frontend: Lista de eventos (panel admin)",
  "descripcion": "Página /admin/eventos con tabla de todos los eventos del admin. Mostrar nombre, fecha, estado (con badge de color), cantidad de badges y acciones (ver, editar, cambiar estado). Botón destacado para crear nuevo evento.",
  "modulo": "eventos",
  "sprint": 2,
  "prioridad": "alta",
  "estado": "pendiente",
  "horas_estimadas": 4,
  "asignado_a": null,
  "dependencias": ["EVENTO-002", "AUTH-007"],
  "criterios_aceptacion": [
    "Tabla lista los eventos del admin autenticado",
    "Estado del evento visible con color (verde=activo, gris=borrador, rojo=finalizado)",
    "Paginación funciona",
    "Carga inicial muestra skeleton loader"
  ]
}
```

```json
{
  "codigo": "EVENTO-007",
  "titulo": "Frontend: Formulario crear y editar evento",
  "descripcion": "Página /admin/eventos/nuevo y /admin/eventos/:id/editar con formulario completo. Campos: nombre, descripción (textarea), fecha (date picker), lugar, capacidad. Validación en cliente antes de enviar. Redirección al listado al guardar.",
  "modulo": "eventos",
  "sprint": 2,
  "prioridad": "alta",
  "estado": "pendiente",
  "horas_estimadas": 5,
  "asignado_a": null,
  "dependencias": ["EVENTO-001", "EVENTO-004"],
  "criterios_aceptacion": [
    "Formulario pre-llena datos al editar",
    "Errores de validación se muestran por campo",
    "Botón de guardar deshabilitado durante el request",
    "Al guardar exitosamente redirige con toast de confirmación"
  ]
}
```

---

### Módulo: `qr`

```json
{
  "codigo": "QR-001",
  "titulo": "Endpoint: Crear badge con QR",
  "descripcion": "POST /api/eventos/:eventoId/badges — Solo admin. Recibir nombre, descripción, imagen_url, límite_redencion. Generar un qr_token UUID v4 único. Generar la imagen QR con la librería qrcode (data URL). Guardar todo en la colección badges.",
  "modulo": "qr",
  "sprint": 2,
  "prioridad": "critica",
  "estado": "pendiente",
  "horas_estimadas": 4,
  "asignado_a": null,
  "dependencias": ["EVENTO-001", "AUTH-004", "SETUP-004"],
  "criterios_aceptacion": [
    "Retorna 201 con el badge creado incluyendo qr_token y qr_imagen_url",
    "qr_token es único (índice único en MongoDB)",
    "La imagen QR es un data URL válido (base64 PNG)",
    "El badge queda asociado al evento correcto"
  ]
}
```

```json
{
  "codigo": "QR-002",
  "titulo": "Endpoint: Listar badges de un evento",
  "descripcion": "GET /api/eventos/:eventoId/badges — Autenticado. Retornar todos los badges del evento con su progreso de redención (total_redimidos / limite_redencion). Incluir el QR como data URL para mostrarlo en el panel admin.",
  "modulo": "qr",
  "sprint": 2,
  "prioridad": "alta",
  "estado": "pendiente",
  "horas_estimadas": 2,
  "asignado_a": null,
  "dependencias": ["QR-001"],
  "criterios_aceptacion": [
    "Retorna array de badges del evento con conteo de redenciones",
    "Incluye porcentaje de progreso calculado"
  ]
}
```

```json
{
  "codigo": "QR-003",
  "titulo": "Endpoint: Validar y redimir badge por QR token",
  "descripcion": "POST /api/redencion/:qrToken — Asistente autenticado. Buscar el badge por qr_token. Verificar que: (1) el badge existe y está activo, (2) el evento está activo, (3) el usuario no ha redimido este badge antes, (4) no se ha alcanzado el límite de redencion. Si todo pasa, crear documento en redenciones e incrementar total_redimidos. Emitir evento Socket.io 'badge_redimido'.",
  "modulo": "qr",
  "sprint": 2,
  "prioridad": "critica",
  "estado": "pendiente",
  "horas_estimadas": 5,
  "asignado_a": null,
  "dependencias": ["QR-001", "AUTH-003", "REALTIME-001"],
  "criterios_aceptacion": [
    "Retorna 200 con datos del badge ganado",
    "Retorna 409 si el usuario ya redimió este badge",
    "Retorna 410 si el badge alcanzó su límite",
    "Retorna 404 si el token no existe",
    "Retorna 403 si el evento no está activo",
    "La redención es atómica (no se crea duplicado bajo carga concurrente)"
  ]
}
```

```json
{
  "codigo": "QR-004",
  "titulo": "Frontend: Vista del QR generado (panel admin)",
  "descripcion": "Dentro de la pantalla de detalle de evento, mostrar cada badge con su imagen QR. Botón para descargar el QR como PNG. Mostrar nombre del badge, límite de redención y progreso actual. Opción para imprimir QR directamente.",
  "modulo": "qr",
  "sprint": 2,
  "prioridad": "alta",
  "estado": "pendiente",
  "horas_estimadas": 3,
  "asignado_a": null,
  "dependencias": ["QR-002"],
  "criterios_aceptacion": [
    "QR visible y legible en la pantalla",
    "Botón de descarga genera PNG del QR",
    "Progreso de redención actualizado"
  ]
}
```

```json
{
  "codigo": "QR-005",
  "titulo": "Frontend: Pantalla de escaneo de QR (mobile-first)",
  "descripcion": "Página /escanear accesible por asistentes. Activar cámara del dispositivo con react-qr-reader. Al detectar un QR válido, llamar automáticamente al endpoint de redención. Mostrar resultado: badge ganado (éxito) o mensaje de error. Diseñada para usarse en móvil en el evento físico.",
  "modulo": "qr",
  "sprint": 2,
  "prioridad": "critica",
  "estado": "pendiente",
  "horas_estimadas": 6,
  "asignado_a": null,
  "dependencias": ["QR-003", "AUTH-007"],
  "criterios_aceptacion": [
    "La cámara se activa al entrar a la página",
    "Solicita permisos de cámara correctamente",
    "Detección automática del QR sin necesidad de botón",
    "Funciona en Chrome móvil y Safari iOS",
    "Si ya redimió, muestra mensaje específico (no error genérico)",
    "Diseño vertical optimizado para móvil"
  ]
}
```

---

### Módulo: `badges`

```json
{
  "codigo": "BADGE-001",
  "titulo": "Endpoint: Badges del usuario autenticado",
  "descripcion": "GET /api/usuarios/mis-badges — Asistente autenticado. Retornar todos los badges que el usuario ha redimido, con datos del badge y del evento. Incluir fecha de redención. Ordenar por fecha descendente.",
  "modulo": "badges",
  "sprint": 2,
  "prioridad": "alta",
  "estado": "pendiente",
  "horas_estimadas": 2,
  "asignado_a": null,
  "dependencias": ["QR-003", "AUTH-003"],
  "criterios_aceptacion": [
    "Retorna array de redenciones populadas con badge y evento",
    "Solo muestra badges del usuario autenticado",
    "Array vacío si no ha redimido ningún badge (no error)"
  ]
}
```

```json
{
  "codigo": "BADGE-002",
  "titulo": "Frontend: Pantalla de badge ganado con animación",
  "descripcion": "Pantalla que aparece inmediatamente después de una redención exitosa. Mostrar: imagen del badge, nombre, descripción, nombre del evento y mensaje de felicitación. Incluir animación de entrada (confetti o efecto de brillo). Botones para: ver mis badges y escanear otro QR.",
  "modulo": "badges",
  "sprint": 2,
  "prioridad": "critica",
  "estado": "pendiente",
  "horas_estimadas": 5,
  "asignado_a": null,
  "dependencias": ["QR-005", "BADGE-001"],
  "criterios_aceptacion": [
    "Animación visible y fluida al ganar el badge",
    "Imagen del badge grande y centrada",
    "Botones de navegación funcionales",
    "Pantalla accesible desde /badge-ganado/:redencionId"
  ]
}
```

```json
{
  "codigo": "BADGE-003",
  "titulo": "Frontend: Galería de mis badges",
  "descripcion": "Página /mis-badges con grid de todos los badges ganados por el usuario. Mostrar imagen del badge, nombre y fecha de redención. Efecto hover con detalles. Si no tiene badges, mostrar estado vacío con call-to-action para escanear.",
  "modulo": "badges",
  "sprint": 2,
  "prioridad": "alta",
  "estado": "pendiente",
  "horas_estimadas": 4,
  "asignado_a": null,
  "dependencias": ["BADGE-001"],
  "criterios_aceptacion": [
    "Grid responsive (1 columna móvil, 3-4 desktop)",
    "Estado vacío con ilustración y mensaje motivador",
    "Clic en badge muestra detalle",
    "Carga con skeleton loader"
  ]
}
```

---

### Módulo: `frontend`

```json
{
  "codigo": "FRONT-001",
  "titulo": "Layout principal, navbar y rutas protegidas",
  "descripcion": "Crear layout base con navbar que muestre: logo de Lyfter, nombre del usuario y botón de cerrar sesión. Navbar diferente para admin y asistente. Implementar componente ProtectedRoute. Manejar loading state mientras se verifica la sesión.",
  "modulo": "frontend",
  "sprint": 2,
  "prioridad": "critica",
  "estado": "pendiente",
  "horas_estimadas": 4,
  "asignado_a": null,
  "dependencias": ["AUTH-007"],
  "criterios_aceptacion": [
    "Navbar muestra nombre y rol del usuario",
    "Logout funciona y limpia sesión",
    "Rutas /admin/* solo accesibles para admins",
    "Ruta /mis-badges solo accesible para asistentes autenticados",
    "Redirección correcta según rol al intentar acceder a ruta no autorizada"
  ]
}
```

```json
{
  "codigo": "FRONT-002",
  "titulo": "Dashboard principal del administrador",
  "descripcion": "Página /admin/dashboard con resumen: número de eventos activos, total de badges creados, total de redenciones hoy. Cards con acceso rápido a: crear evento, ver eventos, ver estadísticas. Diseño limpio con colores de Lyfter.",
  "modulo": "frontend",
  "sprint": 2,
  "prioridad": "alta",
  "estado": "pendiente",
  "horas_estimadas": 4,
  "asignado_a": null,
  "dependencias": ["FRONT-001", "STATS-001"],
  "criterios_aceptacion": [
    "Cards con métricas cargadas desde la API",
    "Accesos rápidos funcionales",
    "Responsive en móvil y desktop"
  ]
}
```

```json
{
  "codigo": "FRONT-003",
  "titulo": "Sistema global de feedback visual (toasts y loading)",
  "descripcion": "Implementar sistema de notificaciones tipo toast para: éxito, error, info y advertencia. Crear componente de Spinner/Skeleton reutilizable. Manejar estados de carga en todos los botones de acción (deshabilitar y mostrar spinner durante requests).",
  "modulo": "frontend",
  "sprint": 2,
  "prioridad": "alta",
  "estado": "pendiente",
  "horas_estimadas": 3,
  "asignado_a": null,
  "dependencias": ["FRONT-001"],
  "criterios_aceptacion": [
    "Toast visible 3-4 segundos y desaparece solo",
    "Toast de error en rojo, éxito en verde",
    "Botones muestran spinner durante requests y se deshabilitan",
    "Skeleton loaders en todas las listas y tablas"
  ]
}
```

---

## SPRINT 3 — Semana 3: Features Extra + Deploy
> **Objetivo:** Implementar los 4 features adicionales (+40 pts) y desplegar todo en producción con datos reales para la demo.

---

### Módulo: `stats`

```json
{
  "codigo": "STATS-001",
  "titulo": "Endpoint: Estadísticas por evento",
  "descripcion": "GET /api/stats/evento/:id — Solo admin. Retornar: total de asistentes que han redimido al menos un badge, total de redenciones, badge más popular, redenciones por hora (últimas 24h), porcentaje de progreso por badge. Usar agregaciones de MongoDB ($lookup, $group, $count).",
  "modulo": "stats",
  "sprint": 3,
  "prioridad": "alta",
  "estado": "pendiente",
  "horas_estimadas": 5,
  "asignado_a": null,
  "dependencias": ["QR-003", "AUTH-004"],
  "criterios_aceptacion": [
    "Retorna objeto con todas las métricas definidas",
    "Agregaciones usan índices (no full scans)",
    "Tiempo de respuesta menor a 500ms con datos de prueba"
  ]
}
```

```json
{
  "codigo": "STATS-002",
  "titulo": "Endpoint: Estadísticas globales del admin",
  "descripcion": "GET /api/stats/global — Solo admin. Retornar métricas de todos los eventos del admin: total eventos, total badges creados, total redenciones, asistentes únicos. Diseñado para el dashboard principal.",
  "modulo": "stats",
  "sprint": 3,
  "prioridad": "media",
  "estado": "pendiente",
  "horas_estimadas": 3,
  "asignado_a": null,
  "dependencias": ["STATS-001"],
  "criterios_aceptacion": [
    "Retorna métricas globales del admin autenticado",
    "Asistentes únicos no se duplica si redimió varios badges"
  ]
}
```

```json
{
  "codigo": "STATS-003",
  "titulo": "Frontend: Dashboard de estadísticas con gráficos",
  "descripcion": "Página /admin/estadisticas/:eventoId con: gráfico de barras de redenciones por badge (Recharts o Chart.js), línea de tiempo de redenciones por hora, cards de métricas principales, tabla de badges con progreso. Selector de evento en la parte superior.",
  "modulo": "stats",
  "sprint": 3,
  "prioridad": "alta",
  "estado": "pendiente",
  "horas_estimadas": 6,
  "asignado_a": null,
  "dependencias": ["STATS-001", "STATS-002"],
  "criterios_aceptacion": [
    "Gráficos renderizan correctamente con datos reales",
    "Responsive en desktop (gráficos se adaptan)",
    "Selector de evento funcional",
    "Datos se pueden exportar o imprimir (+impresión web)"
  ]
}
```

---

### Módulo: `realtime`

```json
{
  "codigo": "REALTIME-001",
  "titulo": "Backend: Configurar Socket.io",
  "descripcion": "Integrar Socket.io en el servidor Express. Crear rooms por eventoId para que los admins puedan suscribirse a un evento específico. Manejar conexiones y desconexiones. Configurar CORS para Socket.io con los mismos orígenes que Express.",
  "modulo": "realtime",
  "sprint": 3,
  "prioridad": "alta",
  "estado": "pendiente",
  "horas_estimadas": 3,
  "asignado_a": null,
  "dependencias": ["SETUP-005"],
  "criterios_aceptacion": [
    "Socket.io escucha en el mismo puerto que Express",
    "Rooms por eventoId funcionan correctamente",
    "CORS de Socket.io no bloquea el cliente",
    "Log de conexiones/desconexiones visible en consola"
  ]
}
```

```json
{
  "codigo": "REALTIME-002",
  "titulo": "Backend: Emitir evento al redimir badge",
  "descripcion": "En el endpoint de redención (QR-003), después de crear la redención exitosamente, emitir evento Socket.io 'nueva_redencion' al room del evento. El payload debe incluir: badgeId, badgeName, userId, fecha, nuevo total_redimidos.",
  "modulo": "realtime",
  "sprint": 3,
  "prioridad": "alta",
  "estado": "pendiente",
  "horas_estimadas": 2,
  "asignado_a": null,
  "dependencias": ["REALTIME-001", "QR-003"],
  "criterios_aceptacion": [
    "Evento 'nueva_redencion' se emite en cada redención exitosa",
    "Solo llega al room del evento correcto",
    "La emisión no bloquea el response HTTP"
  ]
}
```

```json
{
  "codigo": "REALTIME-003",
  "titulo": "Frontend: Contador de progreso en tiempo real",
  "descripcion": "En el dashboard del admin y en la vista de un evento, conectar Socket.io y escuchar el evento 'nueva_redencion'. Actualizar los contadores y barras de progreso en tiempo real sin recargar la página. Mostrar notificación discreta cuando se gana un badge.",
  "modulo": "realtime",
  "sprint": 3,
  "prioridad": "alta",
  "estado": "pendiente",
  "horas_estimadas": 4,
  "asignado_a": null,
  "dependencias": ["REALTIME-002", "STATS-003"],
  "criterios_aceptacion": [
    "Contador se actualiza en menos de 1 segundo tras la redención",
    "Sin necesidad de recargar la página",
    "Notificación discreta '¡Nuevo badge redimido!' aparece y desaparece",
    "La conexión se reconecta automáticamente si se pierde"
  ]
}
```

---

### Módulo: `historial`

```json
{
  "codigo": "HISTORIAL-001",
  "titulo": "Endpoint: Historial de eventos pasados",
  "descripcion": "GET /api/eventos/historial — Autenticado. Retornar eventos con estado 'finalizado'. Para asistentes: solo eventos donde redimió al menos un badge. Para admins: todos sus eventos finalizados. Incluir métricas básicas (total redenciones, badges creados).",
  "modulo": "historial",
  "sprint": 3,
  "prioridad": "media",
  "estado": "pendiente",
  "horas_estimadas": 3,
  "asignado_a": null,
  "dependencias": ["EVENTO-005", "AUTH-003"],
  "criterios_aceptacion": [
    "Retorna solo eventos finalizados",
    "Asistentes ven eventos donde participaron",
    "Admins ven todos sus eventos finalizados",
    "Incluye métricas básicas de participación"
  ]
}
```

```json
{
  "codigo": "HISTORIAL-002",
  "titulo": "Frontend: Pantalla de historial de eventos",
  "descripcion": "Página /historial con lista de eventos pasados. Para asistentes: mostrar los badges que ganaron en cada evento. Para admins: mostrar resumen de participación de cada evento. Diseño de línea de tiempo o cards por fecha.",
  "modulo": "historial",
  "sprint": 3,
  "prioridad": "media",
  "estado": "pendiente",
  "horas_estimadas": 4,
  "asignado_a": null,
  "dependencias": ["HISTORIAL-001"],
  "criterios_aceptacion": [
    "Lista ordenada del evento más reciente al más antiguo",
    "Vista diferenciada para admin y asistente",
    "Clic en evento lleva al detalle (solo lectura)",
    "Estado vacío si no hay eventos pasados"
  ]
}
```

---

### Módulo: `share`

```json
{
  "codigo": "SHARE-001",
  "titulo": "Generación de imagen del badge para compartir",
  "descripcion": "Crear función que use html2canvas para capturar el componente del badge (imagen + nombre + logo de Lyfter) y convertirlo en una imagen PNG descargable. La imagen debe verse bien en redes sociales (formato 1:1 o 4:5). Agregar marca de agua sutil con el logo de Lyfter.",
  "modulo": "share",
  "sprint": 3,
  "prioridad": "media",
  "estado": "pendiente",
  "horas_estimadas": 4,
  "asignado_a": null,
  "dependencias": ["BADGE-002"],
  "criterios_aceptacion": [
    "La imagen generada incluye badge, nombre y logo de Lyfter",
    "Resolución mínima de 800x800px",
    "Botón de descarga funciona en móvil y desktop",
    "Tiempo de generación menor a 2 segundos"
  ]
}
```

```json
{
  "codigo": "SHARE-002",
  "titulo": "Frontend: Botones de compartir en redes sociales",
  "descripcion": "En la pantalla de badge ganado y en detalle de badge, agregar botones para compartir: (1) Descargar imagen PNG, (2) Compartir con Web Share API (móvil nativo), (3) Compartir en X/Twitter con texto predefinido. Texto: '¡Acabo de ganar el badge [nombre] en el evento de Lyfter! 🏆'",
  "modulo": "share",
  "sprint": 3,
  "prioridad": "media",
  "estado": "pendiente",
  "horas_estimadas": 3,
  "asignado_a": null,
  "dependencias": ["SHARE-001"],
  "criterios_aceptacion": [
    "Web Share API funciona en Chrome móvil",
    "Fallback a descarga si Web Share API no está disponible",
    "Link de Twitter abre con texto y hashtag #Lyfter prellenado",
    "Botones visualmente claros con iconos de cada red"
  ]
}
```

---

### Módulo: `deploy`

```json
{
  "codigo": "DEPLOY-001",
  "titulo": "Configurar MongoDB Atlas para producción",
  "descripcion": "En el cluster de Atlas: crear usuario dedicado para producción (diferente al de desarrollo), configurar IP Whitelist para permitir Railway (0.0.0.0/0 o IPs específicas), habilitar backups automáticos, crear índices de producción. Documentar la URI de conexión de producción.",
  "modulo": "deploy",
  "sprint": 3,
  "prioridad": "critica",
  "estado": "pendiente",
  "horas_estimadas": 2,
  "asignado_a": null,
  "dependencias": ["SETUP-002"],
  "criterios_aceptacion": [
    "Usuario de producción con contraseña fuerte y distinta a dev",
    "Conexión desde Railway funciona",
    "Backups automáticos habilitados",
    "Todos los índices creados en el cluster de producción"
  ]
}
```

```json
{
  "codigo": "DEPLOY-002",
  "titulo": "Deploy del backend en Railway",
  "descripcion": "Crear proyecto en Railway. Conectar repositorio de GitHub. Configurar variables de entorno de producción (MONGODB_URI, JWT_SECRET, CLIENT_URL, NODE_ENV=production). Verificar que el Procfile o el package.json start script esté correcto. Obtener URL pública del backend.",
  "modulo": "deploy",
  "sprint": 3,
  "prioridad": "critica",
  "estado": "pendiente",
  "horas_estimadas": 3,
  "asignado_a": null,
  "dependencias": ["DEPLOY-001", "SETUP-003"],
  "criterios_aceptacion": [
    "GET https://[url-railway]/api/health retorna { status: 'ok' }",
    "Variables de entorno configuradas (no hardcodeadas)",
    "Logs de Railway sin errores al iniciar",
    "Auto-deploy en push a rama main configurado"
  ]
}
```

```json
{
  "codigo": "DEPLOY-003",
  "titulo": "Deploy del frontend en Vercel",
  "descripcion": "Importar proyecto Next.js en Vercel. Configurar variable de entorno NEXT_PUBLIC_API_URL con la URL de Railway. Verificar que el build de Next.js pase sin errores. Obtener URL pública del frontend.",
  "modulo": "deploy",
  "sprint": 3,
  "prioridad": "critica",
  "estado": "pendiente",
  "horas_estimadas": 2,
  "asignado_a": null,
  "dependencias": ["DEPLOY-002"],
  "criterios_aceptacion": [
    "Build de Vercel exitoso (cero errores de TypeScript o ESLint que fallen build)",
    "NEXT_PUBLIC_API_URL apunta a la URL de Railway",
    "Página de login carga correctamente en la URL de Vercel",
    "Auto-deploy en push a rama main"
  ]
}
```

```json
{
  "codigo": "DEPLOY-004",
  "titulo": "Configurar CORS de producción",
  "descripcion": "Actualizar la configuración de CORS en el servidor para permitir la URL de Vercel además de localhost. Verificar que Socket.io también tenga CORS correcto para la URL de Vercel. Probar desde la URL pública de Vercel que los requests al backend funcionan.",
  "modulo": "deploy",
  "sprint": 3,
  "prioridad": "critica",
  "estado": "pendiente",
  "horas_estimadas": 1,
  "asignado_a": null,
  "dependencias": ["DEPLOY-002", "DEPLOY-003"],
  "criterios_aceptacion": [
    "Sin errores de CORS en el browser desde la URL de Vercel",
    "Socket.io se conecta correctamente desde Vercel",
    "Requests a la API responden correctamente"
  ]
}
```

```json
{
  "codigo": "DEPLOY-005",
  "titulo": "Prueba integral del flujo completo en producción",
  "descripcion": "Ejecutar el flujo completo desde producción: (1) login admin, (2) crear evento, (3) crear badge y generar QR, (4) login asistente en otro dispositivo, (5) escanear QR con cámara del celular, (6) ver badge ganado, (7) compartir badge. Documentar cualquier bug encontrado y corregirlo.",
  "modulo": "deploy",
  "sprint": 3,
  "prioridad": "critica",
  "estado": "pendiente",
  "horas_estimadas": 4,
  "asignado_a": null,
  "dependencias": ["DEPLOY-004"],
  "criterios_aceptacion": [
    "Flujo completo sin errores críticos",
    "Escaneo de QR funciona desde celular con la URL de producción",
    "Socket.io en tiempo real funciona en producción",
    "No hay datos hardcodeados ni referencias a localhost"
  ]
}
```

```json
{
  "codigo": "DEPLOY-006",
  "titulo": "Insertar datos reales de demo",
  "descripcion": "Crear script seed (server/scripts/seed.js) para insertar datos realistas: 1 admin (Lyfter), 1 evento 'Lyfter Fest 2026', 5-8 badges temáticos con imágenes reales, 10-15 asistentes de prueba con redenciones variadas. Ejecutar el seed en producción antes de la demo.",
  "modulo": "deploy",
  "sprint": 3,
  "prioridad": "alta",
  "estado": "pendiente",
  "horas_estimadas": 3,
  "asignado_a": null,
  "dependencias": ["DEPLOY-005"],
  "criterios_aceptacion": [
    "Script seed es idempotente (no duplica datos si se ejecuta dos veces)",
    "Los datos se ven reales y profesionales (no 'test123')",
    "Los gráficos de estadísticas muestran datos significativos",
    "Credenciales del admin de demo documentadas para la presentación"
  ]
}
```

```json
{
  "codigo": "DEPLOY-007",
  "titulo": "Preparar guión y flujo de presentación",
  "descripcion": "Documentar el flujo exacto de la demo: qué usuario inicia sesión primero, en qué orden se muestran las pantallas, quién escanea el QR, cómo se muestra el tiempo real. Cada integrante debe conocer la parte del código que le corresponde para responder preguntas técnicas. Hacer al menos 2 ensayos completos.",
  "modulo": "deploy",
  "sprint": 3,
  "prioridad": "alta",
  "estado": "pendiente",
  "horas_estimadas": 3,
  "asignado_a": null,
  "dependencias": ["DEPLOY-006"],
  "criterios_aceptacion": [
    "Guión escrito con pasos numerados",
    "Cada integrante tiene asignada una sección técnica para defender",
    "Demo completa en menos de 10 minutos",
    "Plan de contingencia si algo falla (screenshots de backup)"
  ]
}
```

---

## Resumen de Tasks por Sprint

| Sprint | Tareas | Horas estimadas | Objetivo |
|---|---|---|---|
| Sprint 1 | 12 tareas | ~31 hrs | Fundación, auth, modelos |
| Sprint 2 | 19 tareas | ~52 hrs | Core: eventos, QR, badges, frontend |
| Sprint 3 | 17 tareas | ~55 hrs | Extra features + deploy + demo |
| **Total** | **48 tareas** | **~138 hrs** | **~27.6 hrs por integrante** |

## Distribución Sugerida por Integrante

| Integrante | Módulos principales |
|---|---|
| Backend Lead | SETUP, AUTH-001 al 005, EVENTO-001 al 005 |
| Backend Dev | QR-001 al 003, BADGE-001, STATS-001 al 002, HISTORIAL-001 |
| Frontend Lead | AUTH-006 al 007, FRONT-001 al 003, EVENTO-006 al 007 |
| Frontend Dev | QR-004 al 005, BADGE-002 al 003, HISTORIAL-002, SHARE-001 al 002 |
| DevOps / Full-stack | REALTIME-001 al 003, STATS-003, DEPLOY-001 al 007 |
