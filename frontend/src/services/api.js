import axios from 'axios'
import { mockApi } from './mockApi'

// Demo mode: serve built-in sample data so every screen is previewable before the
// Flask API exists. Flip VITE_USE_MOCK to "false" once the backend is running.
export const isMock = import.meta.env.VITE_USE_MOCK === 'true'

// Normalize an Axios error into a user-facing string. Maps network failures and 503s to a
// Render cold-start hint (per session instructions); never leaks raw error objects.
export function readApiError(e, fallback = 'Something went wrong. Please try again.') {
  if (e?.response?.data?.error) return e.response.data.error
  if (!e?.response || e.response.status === 503) {
    return 'The server may be starting up — please try again in a moment.'
  }
  return fallback
}

function createRealApi() {
  const instance = axios.create({
    baseURL: import.meta.env.VITE_API_URL,
    timeout: 15000,
  })

  // Attach the JWT to every request.
  instance.interceptors.request.use((config) => {
    const token = localStorage.getItem('token')
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
  })

  // On an expired/invalid session, clear auth and bounce to login.
  instance.interceptors.response.use(
    (response) => response,
    async (error) => {
      if (error.response?.status === 401) {
        const { useAuthStore } = await import('@/stores/auth')
        useAuthStore().logout()
        const { default: router } = await import('@/router')
        if (router.currentRoute.value.path !== '/login') router.push('/login')
      }
      return Promise.reject(error)
    },
  )

  return instance
}

export const api = isMock ? mockApi : createRealApi()
