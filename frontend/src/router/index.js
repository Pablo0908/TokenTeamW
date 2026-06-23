import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useOrgContextStore } from '@/stores/orgContext'

const routes = [
  { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue'), meta: { public: true } },
  { path: '/register', name: 'register', component: () => import('@/views/RegisterView.vue'), meta: { public: true } },
  { path: '/forgot-password', name: 'forgot-password', component: () => import('@/views/ForgotPasswordView.vue'), meta: { public: true } },

  { path: '/', name: 'home', component: () => import('@/views/HomeView.vue'), meta: { requiresAuth: true } },
  { path: '/scan', name: 'scan', component: () => import('@/views/ScanView.vue'), meta: { requiresAuth: true } },
  { path: '/badges', name: 'badges', component: () => import('@/views/BadgesView.vue'), meta: { requiresAuth: true } },
  { path: '/events', name: 'events', component: () => import('@/views/EventsView.vue'), meta: { requiresAuth: true } },
  { path: '/events/:id', name: 'event-detail', component: () => import('@/views/EventDetailView.vue'), meta: { requiresAuth: true } },
  { path: '/profile', name: 'profile', component: () => import('@/views/ProfileView.vue'), meta: { requiresAuth: true } },
  { path: '/invites', name: 'invites', component: () => import('@/views/InvitesView.vue'), meta: { requiresAuth: true } },

  // Public QR landing — redirects to login then back (handled inside the view).
  { path: '/redeem/:eventId/:token', name: 'redeem', component: () => import('@/views/RedeemView.vue'), meta: { public: true } },

  // Platform panel — super-admin only (global events/users/audit across all orgs).
  { path: '/admin/events', name: 'admin-events', component: () => import('@/views/admin/AdminEventsView.vue'), meta: { requiresAuth: true, requiresSuperAdmin: true } },
  { path: '/admin/users', name: 'admin-users', component: () => import('@/views/admin/AdminUsersView.vue'), meta: { requiresAuth: true, requiresSuperAdmin: true } },
  { path: '/admin/users/:id', name: 'admin-user-detail', component: () => import('@/views/admin/AdminUserDetailView.vue'), meta: { requiresAuth: true, requiresSuperAdmin: true } },
  // /new must come before /:id so Vue Router doesn't treat "new" as an event ID.
  { path: '/admin/events/new', name: 'admin-event-new', component: () => import('@/views/admin/AdminEventNewView.vue'), meta: { requiresAuth: true, requiresSuperAdmin: true } },
  { path: '/admin/events/:id', name: 'admin-event-detail', component: () => import('@/views/admin/AdminEventDetailView.vue'), meta: { requiresAuth: true, requiresSuperAdmin: true } },
  { path: '/admin/audit', name: 'admin-audit', component: () => import('@/views/admin/AdminAuditView.vue'), meta: { requiresAuth: true, requiresSuperAdmin: true } },
  { path: '/admin/org-invites', name: 'admin-org-invites', component: () => import('@/views/admin/AdminOrgInvitesView.vue'), meta: { requiresAuth: true, requiresSuperAdmin: true } },

  // Org-scoped panel — any member of the active org (tabs gate by role in-view).
  { path: '/org/:tab(events|members|participants|audit|settings)?', name: 'org-panel', component: () => import('@/views/OrgPanelView.vue'), meta: { requiresAuth: true, requiresOrgMember: true } },

  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  scrollBehavior: () => ({ top: 0 }),
  routes,
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    auth.setRedirect(to.fullPath)
    return { name: 'login' }
  }

  // Logged-in users shouldn't see auth screens — send them to their home surface.
  if ((to.name === 'login' || to.name === 'register') && auth.isAuthenticated) {
    return { name: 'home' }
  }

  // Platform (super-admin) and org-scoped panels authorize on the org context, not the
  // legacy global role — so an org owner who is a platform attendee still gets in.
  if (to.meta.requiresSuperAdmin || to.meta.requiresOrgMember) {
    const org = useOrgContextStore()
    await org.ensureLoaded()
    if (to.meta.requiresSuperAdmin && !org.isSuperAdmin) {
      return org.isOrgMember ? { name: 'org-panel' } : { name: 'home' }
    }
    if (to.meta.requiresOrgMember && !org.isOrgMember && !org.isSuperAdmin) {
      return { name: 'home' }
    }
  }

  return true
})

export default router
