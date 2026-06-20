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

  // 2FA intermediate state: set while OTP is pending, cleared after verify or cancel.
  const pendingEmail = ref(null)

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => role.value === 'admin')
  const isAssistant = computed(() => role.value === 'assistant')
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
    if (token.value) localStorage.setItem('token', token.value)
    else localStorage.removeItem('token')
    if (role.value) localStorage.setItem('role', role.value)
    else localStorage.removeItem('role')
    if (user.value) localStorage.setItem('user', JSON.stringify(user.value))
    else localStorage.removeItem('user')
  }

  function _applySession(data, email) {
    token.value = data.token
    role.value = data.role ?? data.user?.role ?? 'attendee'
    user.value = data.user ?? { email, role: role.value }
    persist()
  }

  // Returns true (logged in), 'otp' (code sent, show OTP step), or false (error).
  async function login(credentials) {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.post('/auth/login', credentials)

      if (data.requires_2fa) {
        pendingEmail.value = credentials.email
        return 'otp'
      }

      // Server returned a token directly (no 2FA configured on this account).
      _applySession(data, credentials.email)
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

  // Verifies the OTP after the first login step. Returns true or false.
  async function verify2fa(email, code) {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.post('/auth/verify-2fa', { email, code })
      pendingEmail.value = null
      _applySession(data, email)
      const { useSettingsStore } = await import('@/stores/settings')
      useSettingsStore().hydrate(data.user?.preferences)
      return true
    } catch (e) {
      error.value = readApiError(e, t('errors.verify2fa'))
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
    pendingEmail.value = null
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
    pendingEmail,
    isAuthenticated,
    isAdmin,
    isAssistant,
    isStaff,
    displayName,
    loadFromStorage,
    login,
    verify2fa,
    register,
    logout,
    setRedirect,
    consumeRedirect,
  }
})
