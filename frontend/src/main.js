import { createApp } from 'vue'
import { createPinia, setActivePinia } from 'pinia'
// Brand fonts (self-hosted for offline PWA): Space Grotesk (display) + Montserrat (body).
import '@fontsource/space-grotesk/500.css'
import '@fontsource/space-grotesk/600.css'
import '@fontsource/space-grotesk/700.css'
import '@fontsource/montserrat/400.css'
import '@fontsource/montserrat/500.css'
import '@fontsource/montserrat/600.css'
import App from './App.vue'
import router from './router'
import './style.css'
import { i18n } from './i18n'
import { useAuthStore } from './stores/auth'

const app = createApp(App)
const pinia = createPinia()

setActivePinia(pinia)
app.use(pinia)
app.use(i18n)

// Rehydrate the session from localStorage before the router guard runs.
useAuthStore().loadFromStorage()

app.use(router)
app.mount('#app')
