import { ref } from 'vue'

// Lightweight i18n: a reactive, persisted locale + a t(key, params) lookup.
// English is the default; Spanish is Latin-American neutral.
const STORAGE_KEY = 'lyfter_locale'
export const SUPPORTED = ['en', 'es']

const en = {
  common: {
    close: 'Close', cancel: 'Cancel', back: 'Back', logout: 'Log out',
    seeAll: 'see all', none: 'None', loading: 'Loading…',
  },
  nav: { home: 'Home', scan: 'Scan', badges: 'Badges', events: 'Events', profile: 'Profile' },
  auth: {
    loginTitle: 'Welcome back',
    loginSubtitle: 'Sign in to keep collecting badges.',
    registerTitle: 'Create your account',
    registerSubtitle: 'Start collecting badges in seconds.',
    email: 'Email', password: 'Password', firstName: 'First name', lastName: 'Last name',
    confirmPassword: 'Confirm password',
    signIn: 'Sign in', signingIn: 'Signing in…',
    create: 'Create account', creating: 'Creating…',
    newHere: 'New here?', createLink: 'Create an account',
    haveAccount: 'Already have an account?', signInLink: 'Sign in',
    errEmail: 'Enter a valid email.', errEmailTaken: 'That email is already registered. Try signing in.', errPasswordRequired: 'Password is required.',
    errPassword6: 'At least 6 characters.', errMatch: "Passwords don't match.",
    errPasswordWeak: 'Password does not meet the requirements.',
    pwdLen: '8+ characters', pwdUpper: 'One uppercase letter',
    pwdLower: 'One lowercase letter', pwdNumber: 'One number',
    pwdSpecial: 'One special character (!@#$…)',
    twoFaTitle: 'Verify your identity',
    twoFaSubtitle: 'We sent a 6-digit code to {email}. Enter it below.',
    otpLabel: 'Verification code',
    otpPlaceholder: '000000',
    verify: 'Verify', verifying: 'Verifying…',
    resend: 'Resend code', resending: 'Resending…',
    backToSignIn: 'Back to sign in',
    errOtpRequired: 'Enter the 6-digit code.',
    otpSent: 'A new code has been sent to your email.',
    forgotPassword: 'Forgot password?',
    forgotTitle: 'Reset your password',
    forgotSubtitle: 'Enter your email and we\'ll send you a reset code.',
    forgotSubmit: 'Send reset code', forgotSubmitting: 'Sending…',
    forgotSent: 'Check your email — we sent a 6-digit code to {email}.',
    resetTitle: 'Set a new password',
    resetCodeLabel: 'Reset code',
    newPasswordLabel: 'New password',
    resetSubmit: 'Reset password', resetSubmitting: 'Resetting…',
    resetSuccess: 'Password updated! You can now sign in.',
    resendReset: 'Resend code',
  },
  home: {
    greeting: 'Hey, {name}',
    newBadgeOne: '{n} new badge this week',
    newBadgeMany: '{n} new badges this week',
    scanTitle: 'Scan a QR code', scanSub: 'Point at any event badge station',
    badges: 'Badges', events: 'Events', streak: 'Streak',
    noBadges: 'No badges yet — scan your first one!', loading: 'Loading your badges…',
  },
  badges: {
    title: 'Badges & Events',
    summary: '{earned} earned · {completed} events completed',
    loading: 'Loading your collection…',
    emptyTitle: 'No badges yet',
    emptySub: 'Scan a QR at an event station to earn your first badge.',
    emptyCta: 'Start scanning',
    notEarned: '🔒 Not earned yet — scan this badge to unlock it.',
    download: 'Download image',
  },
  share: {
    heading: 'Share this badge', copyLink: 'Copy link', copied: 'Link copied!',
    copiedIn: 'Link copied — paste it in {app}', more: 'More',
  },
  events: {
    title: 'Events', all: 'All', active: 'Active', past: 'Past',
    loading: 'Loading events…', empty: 'No events to show.',
    status: { completed: 'Completed', active: 'Active', upcoming: 'Upcoming', past: 'Past', event: 'Event' },
    dateTba: 'Date TBA', progress: 'Progress', unitBadges: 'badges',
  },
  eventDetail: {
    loading: 'Loading event…', yourProgress: 'Your progress', completed: 'Completed',
    prizeUnlocked: 'Prize unlocked', prizeLocked: 'Complete all badges to unlock',
    prizeDefault: 'A special reward', badges: 'Badges',
    noBadges: 'No badges have been added to this event yet.',
  },
  profile: {
    organizer: 'Organizer', attendee: 'Attendee', assistant: 'Assistant',
    badges: 'Badges', events: 'Events', done: 'Done',
    progressByEvent: 'Progress by event', openAdmin: 'Open organizer panel',
    language: 'Language',
    editProfile: 'Edit profile', saveProfile: 'Save', cancelEdit: 'Cancel',
    username: 'Username', usernamePlaceholder: 'e.g. valentina_23',
    usernameHint: '3–20 characters: letters, numbers, underscores.',
    usernameAvailable: 'Available', usernameTaken: 'Already taken', usernameInvalid: 'Invalid format',
    bio: 'Bio', bioPlaceholder: 'Tell people a little about yourself…',
    bioLimit: '{n}/160',
    photo: 'Photo', changePhoto: 'Change photo',
    pinnedBadges: 'Pinned badges', managePins: 'Manage pins',
    noPins: 'No pinned badges yet.', pinHint: 'Pick up to 4 favorites from your collection.',
    noEarned: 'Earn badges to pin them here.',
    saving: 'Saving…',
  },
  settings: {
    title: 'Settings',
    language: 'Language',
    lightMode: 'Light mode', lightModeHint: 'Use a light theme (dark by default).',
    effects: 'Extra effects', effectsHint: 'Animations, glow and confetti.',
    appearance: 'Appearance', appearanceHint: 'Theme, effects & colors',
    saturation: 'Color saturation', contrast: 'Color contrast',
    reset: 'Reset to defaults',
    changePassword: 'Change password', changePasswordHint: 'Update your account password',
    changePasswordEmailStep: 'Enter your account email to receive a verification code.',
    changePasswordSendCode: 'Send code', changePasswordSending: 'Sending…',
    changePasswordCodeSent: 'Code sent to {email}. Enter it below.',
    newPassword: 'New password',
    changePasswordSubmit: 'Update password', changePasswordSubmitting: 'Updating…',
    changePasswordSuccess: 'Password updated successfully.',
    errEmailMismatch: 'Email does not match your account.',
    accessibility: 'Accessibility', accessibilityHint: 'Text, contrast & interaction',
    textReadability: 'Text & Readability',
    colorContrast: 'Color & Contrast',
    motorInteraction: 'Motor & Interaction',
    fontSize: 'Font size',
    dyslexiaFont: 'Dyslexia-friendly font', dyslexiaFontHint: 'Atkinson Hyperlegible',
    lineSpacing: 'Increased line spacing', lineSpacingHint: '1.5 → 1.9 line height',
    boldText: 'Bold text', boldTextHint: 'Heavier weight throughout',
    preview: 'Preview',
    previewText: 'Scan a QR code to collect your badge at the Lyfter event.',
    autoTheme: 'Follow system dark mode', autoThemeHint: 'Auto-switches with OS setting',
    highContrast: 'High contrast', highContrastHint: 'Stronger borders & text',
    colorBlind: 'Color-blind safe palette', colorBlindHint: 'Deuteranopia-optimized',
    contrastLevel: 'Contrast level',
    low: 'Low', high: 'High',
    largeTapTargets: 'Large tap targets', largeTapTargetsHint: 'Bigger buttons & touch zones',
    focusHighlight: 'Focus highlight', focusHighlightHint: 'Visible ring on focused element',
  },
  scan: {
    title: 'Scan badges', heading: 'Scan to earn', sub: 'Point at any QR at an event station',
    tryAgain: 'Try camera again', simulate: 'Simulate a scan (demo)',
    notLyfter: 'This QR code is not a Lyfter badge. Try again.',
    errInsecure: `Your phone's browser blocks the camera on insecure (http://) pages, so it can't ask for permission. Open the app over HTTPS (or on the computer at localhost) to scan QR codes.`,
    errDenied: `Camera permission is blocked. Tap the camera (or 🔒) icon in your browser's address bar, set Camera to “Allow”, then press “Try camera again”.`,
    errNotFound: 'No camera was found on this device.',
    errBusy: `Another app is using the camera. Close it, then press “Try camera again”.`,
    errGeneric: `Couldn't start the camera. Press “Try camera again”.`,
    failTitle: 'Scan failed',
  },
  redeem: { working: 'Redeeming your badge…', failTitle: 'Could not redeem', viewCollection: 'View my collection', scanAnother: 'Scan another' },
  outcome: {
    badgeEarned: 'Badge earned!', eventCompleted: 'Event completed!',
    duplicateTitle: 'Already collected', duplicateMsg: 'You already have this badge.',
    notAvailableTitle: 'Not available', notAvailableMsg: "This badge isn't available right now.",
    limitTitle: 'No longer available', limitMsg: 'This badge has reached its limit.',
    sessionTitle: 'Session expired', sessionMsg: 'Please sign in again to continue.',
    genericMsg: 'Something went wrong. Please try again.', prizeUnlocked: 'Prize unlocked',
    queuedTitle: 'Saved offline', queuedMsg: "No connection — this badge will be added automatically when you're back online.",
  },
  queue: {
    pendingOne: '1 scan waiting to sync', pendingMany: '{n} scans waiting to sync',
    syncedOne: 'Synced 1 queued badge.', syncedMany: 'Synced {n} queued badges.',
    syncFailed: "Some queued scans couldn't be redeemed.",
  },
  rarity: {
    legendary: 'Legendary', epic: 'Epic', rare: 'Rare', common: 'Common',
    collectedOne: '1 collected', collectedMany: '{n} collected', tapToFlip: 'Tap the badge for details',
  },
  welcome: {
    greeting: 'Welcome to Lyfter! 👋',
    question: 'Which language would you like to use?',
    english: 'English', spanish: 'Español', continue: 'Continue',
  },
  coach: {
    scanTitle: 'Scan badges', scanBody: 'Tap here to open the camera and scan a QR at any booth to earn a badge.',
    badgesTitle: 'Your badges', badgesBody: 'Badges you earn show up here — tap one to view or share it.',
    eventsTitle: 'Events', eventsBody: 'Browse events and track your progress toward each prize.',
    gotIt: 'Got it',
  },
  errors: {
    signIn: 'Could not sign in. Check your credentials.',
    verify2fa: 'Incorrect or expired code. Try again.',
    register: 'Could not create your account.',
    events: 'Could not load events. Please try again.',
    event: 'Could not load the event.',
    badges: 'Could not load your badges.',
    coldStart: 'The server may be starting up — please try again in a moment.',
    generic: 'Something went wrong. Please try again.',
  },
}

const es = {
  common: {
    close: 'Cerrar', cancel: 'Cancelar', back: 'Atrás', logout: 'Cerrar sesión',
    seeAll: 'ver todo', none: 'Ninguno', loading: 'Cargando…',
  },
  nav: { home: 'Inicio', scan: 'Escanear', badges: 'Insignias', events: 'Eventos', profile: 'Perfil' },
  auth: {
    loginTitle: 'Bienvenido de nuevo',
    loginSubtitle: 'Inicia sesión para seguir coleccionando insignias.',
    registerTitle: 'Crea tu cuenta',
    registerSubtitle: 'Empieza a coleccionar insignias en segundos.',
    email: 'Correo', password: 'Contraseña', firstName: 'Nombre', lastName: 'Apellido',
    confirmPassword: 'Confirmar contraseña',
    signIn: 'Iniciar sesión', signingIn: 'Iniciando sesión…',
    create: 'Crear cuenta', creating: 'Creando…',
    newHere: '¿Nuevo por aquí?', createLink: 'Crea una cuenta',
    haveAccount: '¿Ya tienes una cuenta?', signInLink: 'Inicia sesión',
    errEmail: 'Ingresa un correo válido.', errEmailTaken: 'Ese correo ya está registrado. Intenta iniciar sesión.', errPasswordRequired: 'La contraseña es obligatoria.',
    errPassword6: 'Al menos 6 caracteres.', errMatch: 'Las contraseñas no coinciden.',
    errPasswordWeak: 'La contraseña no cumple los requisitos.',
    pwdLen: '8+ caracteres', pwdUpper: 'Una letra mayúscula',
    pwdLower: 'Una letra minúscula', pwdNumber: 'Un número',
    pwdSpecial: 'Un carácter especial (!@#$…)',
    twoFaTitle: 'Verifica tu identidad',
    twoFaSubtitle: 'Enviamos un código de 6 dígitos a {email}. Ingrésalo aquí.',
    otpLabel: 'Código de verificación',
    otpPlaceholder: '000000',
    verify: 'Verificar', verifying: 'Verificando…',
    resend: 'Reenviar código', resending: 'Reenviando…',
    backToSignIn: 'Volver al inicio de sesión',
    errOtpRequired: 'Ingresa el código de 6 dígitos.',
    otpSent: 'Se envió un nuevo código a tu correo.',
    forgotPassword: '¿Olvidaste tu contraseña?',
    forgotTitle: 'Recupera tu contraseña',
    forgotSubtitle: 'Ingresa tu correo y te enviaremos un código de recuperación.',
    forgotSubmit: 'Enviar código', forgotSubmitting: 'Enviando…',
    forgotSent: 'Revisa tu correo — enviamos un código de 6 dígitos a {email}.',
    resetTitle: 'Crea una nueva contraseña',
    resetCodeLabel: 'Código de recuperación',
    newPasswordLabel: 'Nueva contraseña',
    resetSubmit: 'Restablecer contraseña', resetSubmitting: 'Restableciendo…',
    resetSuccess: '¡Contraseña actualizada! Ahora puedes iniciar sesión.',
    resendReset: 'Reenviar código',
  },
  home: {
    greeting: 'Hola, {name}',
    newBadgeOne: '{n} insignia nueva esta semana',
    newBadgeMany: '{n} insignias nuevas esta semana',
    scanTitle: 'Escanea un código QR', scanSub: 'Apunta a cualquier estación de insignias del evento',
    badges: 'Insignias', events: 'Eventos', streak: 'Racha',
    noBadges: 'Aún no tienes insignias, ¡escanea la primera!', loading: 'Cargando tus insignias…',
  },
  badges: {
    title: 'Insignias y Eventos',
    summary: '{earned} obtenidas · {completed} eventos completados',
    loading: 'Cargando tu colección…',
    emptyTitle: 'Aún no hay insignias',
    emptySub: 'Escanea un QR en una estación del evento para obtener tu primera insignia.',
    emptyCta: 'Empezar a escanear',
    notEarned: '🔒 Aún no obtenida: escanea esta insignia para desbloquearla.',
    download: 'Descargar imagen',
  },
  share: {
    heading: 'Comparte esta insignia', copyLink: 'Copiar enlace', copied: '¡Enlace copiado!',
    copiedIn: 'Enlace copiado: pégalo en {app}', more: 'Más',
  },
  events: {
    title: 'Eventos', all: 'Todos', active: 'Activos', past: 'Pasados',
    loading: 'Cargando eventos…', empty: 'No hay eventos para mostrar.',
    status: { completed: 'Completado', active: 'Activo', upcoming: 'Próximo', past: 'Pasado', event: 'Evento' },
    dateTba: 'Fecha por definir', progress: 'Progreso', unitBadges: 'insignias',
  },
  eventDetail: {
    loading: 'Cargando evento…', yourProgress: 'Tu progreso', completed: 'Completado',
    prizeUnlocked: 'Premio desbloqueado', prizeLocked: 'Completa todas las insignias para desbloquear',
    prizeDefault: 'Una recompensa especial', badges: 'Insignias',
    noBadges: 'Aún no se han agregado insignias a este evento.',
  },
  profile: {
    organizer: 'Organizador', attendee: 'Participante', assistant: 'Asistente',
    badges: 'Insignias', events: 'Eventos', done: 'Completados',
    progressByEvent: 'Progreso por evento', openAdmin: 'Abrir panel de organizador',
    language: 'Idioma',
    editProfile: 'Editar perfil', saveProfile: 'Guardar', cancelEdit: 'Cancelar',
    username: 'Nombre de usuario', usernamePlaceholder: 'ej. valentina_23',
    usernameHint: '3–20 caracteres: letras, números y guiones bajos.',
    usernameAvailable: 'Disponible', usernameTaken: 'Ya está en uso', usernameInvalid: 'Formato no válido',
    bio: 'Descripción', bioPlaceholder: 'Cuéntale algo a la gente sobre ti…',
    bioLimit: '{n}/160',
    photo: 'Foto', changePhoto: 'Cambiar foto',
    pinnedBadges: 'Insignias destacadas', managePins: 'Gestionar destacados',
    noPins: 'Aún no tienes insignias destacadas.', pinHint: 'Elige hasta 4 favoritas de tu colección.',
    noEarned: 'Gana insignias para destacarlas aquí.',
    saving: 'Guardando…',
  },
  settings: {
    title: 'Configuración',
    language: 'Idioma',
    lightMode: 'Modo claro', lightModeHint: 'Usar un tema claro (oscuro por defecto).',
    effects: 'Efectos adicionales', effectsHint: 'Animaciones, brillo y confeti.',
    appearance: 'Apariencia', appearanceHint: 'Tema, efectos y colores',
    saturation: 'Saturación de color', contrast: 'Contraste de color',
    reset: 'Restablecer valores',
    changePassword: 'Cambiar contraseña', changePasswordHint: 'Actualiza la contraseña de tu cuenta',
    changePasswordEmailStep: 'Ingresa el correo de tu cuenta para recibir un código de verificación.',
    changePasswordSendCode: 'Enviar código', changePasswordSending: 'Enviando…',
    changePasswordCodeSent: 'Código enviado a {email}. Ingrésalo a continuación.',
    newPassword: 'Nueva contraseña',
    changePasswordSubmit: 'Actualizar contraseña', changePasswordSubmitting: 'Actualizando…',
    changePasswordSuccess: 'Contraseña actualizada correctamente.',
    errEmailMismatch: 'El correo no coincide con tu cuenta.',
    accessibility: 'Accesibilidad', accessibilityHint: 'Texto, contraste e interacción',
    textReadability: 'Texto y Legibilidad',
    colorContrast: 'Color y Contraste',
    motorInteraction: 'Motor e Interacción',
    fontSize: 'Tamaño de fuente',
    dyslexiaFont: 'Fuente para dislexia', dyslexiaFontHint: 'Atkinson Hyperlegible',
    lineSpacing: 'Espaciado de línea aumentado', lineSpacingHint: '1.5 → 1.9 de altura de línea',
    boldText: 'Texto en negrita', boldTextHint: 'Mayor peso en toda la app',
    preview: 'Vista previa',
    previewText: 'Escanea un código QR para coleccionar tu insignia en el evento de Lyfter.',
    autoTheme: 'Modo oscuro automático', autoThemeHint: 'Cambia según la configuración del sistema',
    highContrast: 'Alto contraste', highContrastHint: 'Bordes y texto más fuertes',
    colorBlind: 'Paleta para daltonismo', colorBlindHint: 'Optimizada para deuteranopía',
    contrastLevel: 'Nivel de contraste',
    low: 'Bajo', high: 'Alto',
    largeTapTargets: 'Áreas de toque grandes', largeTapTargetsHint: 'Botones y zonas táctiles más grandes',
    focusHighlight: 'Resaltar foco', focusHighlightHint: 'Anillo visible en el elemento enfocado',
  },
  scan: {
    title: 'Escanear insignias', heading: 'Escanea para ganar', sub: 'Apunta a cualquier QR en una estación del evento',
    tryAgain: 'Reintentar cámara', simulate: 'Simular escaneo (demo)',
    notLyfter: 'Este código QR no es una insignia de Lyfter. Inténtalo de nuevo.',
    errInsecure: 'El navegador de tu teléfono bloquea la cámara en páginas no seguras (http://), por lo que no puede pedir permiso. Abre la app por HTTPS (o en la computadora con localhost) para escanear códigos QR.',
    errDenied: 'El permiso de la cámara está bloqueado. Toca el ícono de cámara (o 🔒) en la barra de direcciones, permite la cámara y pulsa “Reintentar cámara”.',
    errNotFound: 'No se encontró cámara en este dispositivo.',
    errBusy: 'Otra app está usando la cámara. Ciérrala y pulsa “Reintentar cámara”.',
    errGeneric: 'No se pudo iniciar la cámara. Pulsa “Reintentar cámara”.',
    failTitle: 'Error al escanear',
  },
  redeem: { working: 'Canjeando tu insignia…', failTitle: 'No se pudo canjear', viewCollection: 'Ver mi colección', scanAnother: 'Escanear otra' },
  outcome: {
    badgeEarned: '¡Insignia obtenida!', eventCompleted: '¡Evento completado!',
    duplicateTitle: 'Ya la tienes', duplicateMsg: 'Ya tienes esta insignia.',
    notAvailableTitle: 'No disponible', notAvailableMsg: 'Esta insignia no está disponible en este momento.',
    limitTitle: 'Ya no está disponible', limitMsg: 'Esta insignia alcanzó su límite.',
    sessionTitle: 'Sesión expirada', sessionMsg: 'Inicia sesión de nuevo para continuar.',
    genericMsg: 'Algo salió mal. Inténtalo de nuevo.', prizeUnlocked: 'Premio desbloqueado',
    queuedTitle: 'Guardado sin conexión', queuedMsg: 'Sin conexión: esta insignia se agregará automáticamente cuando vuelvas a estar en línea.',
  },
  queue: {
    pendingOne: '1 escaneo pendiente de sincronizar', pendingMany: '{n} escaneos pendientes de sincronizar',
    syncedOne: 'Se sincronizó 1 insignia en cola.', syncedMany: 'Se sincronizaron {n} insignias en cola.',
    syncFailed: 'Algunos escaneos en cola no se pudieron canjear.',
  },
  rarity: {
    legendary: 'Legendaria', epic: 'Épica', rare: 'Rara', common: 'Común',
    collectedOne: '1 obtenida', collectedMany: '{n} obtenidas', tapToFlip: 'Toca la insignia para ver detalles',
  },
  welcome: {
    greeting: '¡Bienvenido a Lyfter! 👋',
    question: '¿En qué idioma quieres usar la app?',
    english: 'English', spanish: 'Español', continue: 'Continuar',
  },
  coach: {
    scanTitle: 'Escanea insignias', scanBody: 'Toca aquí para abrir la cámara y escanear un QR en cualquier estación y ganar una insignia.',
    badgesTitle: 'Tus insignias', badgesBody: 'Las insignias que ganes aparecen aquí: toca una para verla o compartirla.',
    eventsTitle: 'Eventos', eventsBody: 'Explora los eventos y sigue tu progreso hacia cada premio.',
    gotIt: 'Entendido',
  },
  errors: {
    signIn: 'No se pudo iniciar sesión. Revisa tus credenciales.',
    verify2fa: 'Código incorrecto o expirado. Inténtalo de nuevo.',
    register: 'No se pudo crear tu cuenta.',
    events: 'No se pudieron cargar los eventos. Inténtalo de nuevo.',
    event: 'No se pudo cargar el evento.',
    badges: 'No se pudieron cargar tus insignias.',
    coldStart: 'El servidor puede estar iniciando — inténtalo de nuevo en un momento.',
    generic: 'Algo salió mal. Inténtalo de nuevo.',
  },
}

const messages = { en, es }

const saved = (typeof localStorage !== 'undefined' && localStorage.getItem(STORAGE_KEY)) || ''
export const locale = ref(SUPPORTED.includes(saved) ? saved : 'en')

// Allow a shareable ?lang=es / ?lang=en link to preset the language.
if (typeof location !== 'undefined') {
  const q = new URLSearchParams(location.search).get('lang')
  if (SUPPORTED.includes(q)) {
    locale.value = q
    try {
      localStorage.setItem(STORAGE_KEY, q)
    } catch {
      /* storage unavailable */
    }
  }
}

function lookup(obj, path) {
  return path.split('.').reduce((o, k) => (o == null ? undefined : o[k]), obj)
}

export function t(key, params) {
  let str = lookup(messages[locale.value], key)
  if (str == null) str = lookup(messages.en, key)
  if (str == null) return key
  if (params) for (const k in params) str = str.replaceAll(`{${k}}`, params[k])
  return str
}

export function setLocale(value) {
  if (!SUPPORTED.includes(value)) return
  locale.value = value
  try {
    localStorage.setItem(STORAGE_KEY, value)
  } catch {
    /* storage unavailable */
  }
  if (typeof document !== 'undefined') document.documentElement.setAttribute('lang', value)
}

export function useLocale() {
  return { locale, t, setLocale }
}

export const i18n = {
  install(app) {
    app.config.globalProperties.$t = t
    if (typeof document !== 'undefined') document.documentElement.setAttribute('lang', locale.value)
  },
}
