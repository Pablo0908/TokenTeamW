import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api, readApiError } from '@/services/api'
import { t } from '@/i18n'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(null)
  const user = ref(null)
  const role = ref(null)
  const error = ref(null)
  const loading = ref(false)
  const redirectAfterLogin = ref(null)

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => role.value === 'admin')
  const isAssistant = computed(() => role.value === 'assistant')
  // Staff = admin or assistant: can reach the organizer screens (assistant is read-only).
  const isStaff = computed(() => role.value === 'admin' || role.value === 'assistant')
  const displayName = computed(() => {
    if (user.value?.name) return user.value.name
    return user.value?.email ? user.value.email.split('@')[0] : 'there'
  })

  function loadFromStorage() {
    token.value = localStorage.getItem('token')
    role.value = localStorage.getItem('role')
    redirectAfterLogin.value = localStorage.getItem('redirectAfterLogin')
    const raw = localStorage.getItem('user')
    user.value = raw ? JSON.parse(raw) : null
  }

  function persist() {
    // Guard against writing the string "null" (which loadFromStorage would read as a session).
    if (token.value) localStorage.setItem('token', token.value)
    else localStorage.removeItem('token')
    if (role.value) localStorage.setItem('role', role.value)
    else localStorage.removeItem('role')
    if (user.value) localStorage.setItem('user', JSON.stringify(user.value))
    else localStorage.removeItem('user')
  }

  async function login(credentials) {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.post('/auth/login', credentials)
      token.value = data.token
      role.value = data.role ?? data.user?.role ?? 'attendee'
      user.value = data.user ?? { email: credentials.email, role: role.value }
      persist()
      // Apply this account's saved appearance preferences (server is source of truth).
      const { useSettingsStore } = await import('@/stores/settings')
      useSettingsStore().hydrate(data.user?.preferences)
      return true
    } catch (e) {
      error.value = readApiError(e, t('errors.signIn'))
      return false
    } finally {
      loading.value = false
    }
  }

  async function register(payload) {
    loading.value = true
    error.value = null
    try {
      await api.post('/auth/register', payload)
      return true
    } catch (e) {
      error.value = readApiError(e, t('errors.register'))
      return false
    } finally {
      loading.value = false
    }
  }

  function logout() {
    token.value = null
    user.value = null
    role.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('role')
    localStorage.removeItem('user')
  }

  function setRedirect(path) {
    redirectAfterLogin.value = path
    localStorage.setItem('redirectAfterLogin', path)
  }

  function consumeRedirect() {
    const target = redirectAfterLogin.value
    redirectAfterLogin.value = null
    localStorage.removeItem('redirectAfterLogin')
    return target
  }

  return {
    token,
    user,
    role,
    error,
    loading,
    redirectAfterLogin,
    isAuthenticated,
    isAdmin,
    isAssistant,
    isStaff,
    displayName,
    loadFromStorage,
    login,
    register,
    logout,
    setRedirect,
    consumeRedirect,
  }
})
