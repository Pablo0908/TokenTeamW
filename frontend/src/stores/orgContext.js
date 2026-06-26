import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/services/api'

// The caller's platform tier + org memberships, driving the platform-vs-org panel
// split and the active-org switcher. Sourced from GET /me/orgs (the JWT is org-free).
export const useOrgContextStore = defineStore('orgContext', () => {
  const platformRole = ref(null)
  const orgs = ref([])
  const activeOrgId = ref(localStorage.getItem('activeOrgId') || null)
  const loaded = ref(false)
  const loading = ref(false)

  const isSuperAdmin = computed(() => platformRole.value === 'super_admin')
  const isOrgMember = computed(() => orgs.value.length > 0)
  const activeOrg = computed(
    () => orgs.value.find((o) => o.id === activeOrgId.value) || orgs.value[0] || null,
  )
  const activeRole = computed(() => activeOrg.value?.role || null)
  const isActiveOwner = computed(() => activeRole.value === 'owner')
  const isActiveAdmin = computed(() => activeRole.value === 'owner' || activeRole.value === 'admin')
  // Any in-org role (owner/admin/staff) — the prize-verifier tier (staff can hand over prizes).
  const isActiveStaff = computed(() => ['owner', 'admin', 'staff'].includes(activeRole.value))

  function persist() {
    if (activeOrgId.value) localStorage.setItem('activeOrgId', activeOrgId.value)
    else localStorage.removeItem('activeOrgId')
  }

  async function load() {
    loading.value = true
    try {
      const { data } = await api.get('/me/orgs')
      platformRole.value = data.platform_role ?? null
      orgs.value = Array.isArray(data.orgs) ? data.orgs : []
      // Keep the active org valid; default to the first one.
      if (!orgs.value.some((o) => o.id === activeOrgId.value)) {
        activeOrgId.value = orgs.value[0]?.id || null
        persist()
      }
    } catch {
      platformRole.value = null
      orgs.value = []
    } finally {
      loaded.value = true
      loading.value = false
    }
    return { isSuperAdmin: isSuperAdmin.value, isOrgMember: isOrgMember.value }
  }

  // Ensures context is loaded once (used by the router guard before deciding access).
  async function ensureLoaded() {
    if (!loaded.value) await load()
  }

  function setActiveOrg(id) {
    activeOrgId.value = id
    persist()
  }

  function reset() {
    platformRole.value = null
    orgs.value = []
    activeOrgId.value = null
    loaded.value = false
    localStorage.removeItem('activeOrgId')
  }

  return {
    platformRole, orgs, activeOrgId, loaded, loading,
    isSuperAdmin, isOrgMember, activeOrg, activeRole, isActiveOwner, isActiveAdmin, isActiveStaff,
    load, ensureLoaded, setActiveOrg, reset,
  }
})
