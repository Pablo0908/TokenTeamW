import { createApp } from 'vue'
import { createPinia, setActivePinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './style.css'
import { useAuthStore } from './stores/auth'

const app = createApp(App)
const pinia = createPinia()

setActivePinia(pinia)
app.use(pinia)

// Rehydrate the session from localStorage before the router guard runs.
useAuthStore().loadFromStorage()

app.use(router)
app.mount('#app')
