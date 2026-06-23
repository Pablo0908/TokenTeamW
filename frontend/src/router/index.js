import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  { path: '/welcome', name: 'welcome', component: () => import('@/views/WelcomeView.vue'), meta: { public: true, fullPage: true } },
  { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue'), meta: { public: true } },
  { path: '/event/:eventId/preview', name: 'event-preview', component: () => import('@/views/EventPreviewView.vue'), meta: { public: true, fullPage: true } },
  { path: '/register', name: 'register', component: () => import('@/views/RegisterView.vue'), meta: { public: true } },
  { path: '/forgot-password', name: 'forgot-password', component: () => import('@/views/ForgotPasswordView.vue'), meta: { public: true } },

  { path: '/', name: 'home', component: () => import('@/views/HomeView.vue'), meta: { requiresAuth: true } },
  { path: '/scan', name: 'scan', component: () => import('@/views/ScanView.vue'), meta: { requiresAuth: true } },
  { path: '/badges', name: 'badges', component: () => import('@/views/BadgesView.vue'), meta: { requiresAuth: true } },
  { path: '/events', name: 'events', component: () => import('@/views/EventsView.vue'), meta: { requiresAuth: true } },
  { path: '/events/:id', name: 'event-detail', component: () => import('@/views/EventDetailView.vue'), meta: { requiresAuth: true } },
  { path: '/profile', name: 'profile', component: () => import('@/views/ProfileView.vue'), meta: { requiresAuth: true } },
  { path: '/profile/security', name: 'profile-security', component: () => import('@/views/ProfileSecurityView.vue'), meta: { requiresAuth: true } },

  // Public QR landing — redirects to login then back (handled inside the view).
  { path: '/redeem/:eventId/:token', name: 'redeem', component: () => import('@/views/RedeemView.vue'), meta: { public: true } },

  // Staff (admin + assistant) can view these; assistant is read-only (enforced in-view + by the API).
  { path: '/admin/events', name: 'admin-events', component: () => import('@/views/admin/AdminEventsView.vue'), meta: { requiresAuth: true, requiresStaff: true } },
  { path: '/admin/users', name: 'admin-users', component: () => import('@/views/admin/AdminUsersView.vue'), meta: { requiresAuth: true, requiresStaff: true } },
  { path: '/admin/users/:id', name: 'admin-user-detail', component: () => import('@/views/admin/AdminUserDetailView.vue'), meta: { requiresAuth: true, requiresStaff: true } },
  // /new must come before /:id so Vue Router doesn't treat "new" as an event ID.
  { path: '/admin/events/new', name: 'admin-event-new', component: () => import('@/views/admin/AdminEventNewView.vue'), meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/admin/events/:id', name: 'admin-event-detail', component: () => import('@/views/admin/AdminEventDetailView.vue'), meta: { requiresAuth: true, requiresStaff: true } },
  // Viewing the audit log is admin-only.
  { path: '/admin/audit', name: 'admin-audit', component: () => import('@/views/admin/AdminAuditView.vue'), meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/admin/announcements', name: 'admin-announcements', component: () => import('@/views/admin/AdminAnnouncementsView.vue'), meta: { requiresAuth: true, requiresAdmin: true } },

  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  scrollBehavior: () => ({ top: 0 }),
  routes,
})

router.beforeEach((to) => {
  const auth = useAuthStore()

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    auth.setRedirect(to.fullPath)
    return { name: 'welcome' }
  }

  if (to.meta.requiresAdmin && !auth.isAdmin) {
    return { name: 'home' }
  }

  if (to.meta.requiresStaff && !auth.isStaff) {
    return { name: 'home' }
  }

  // Logged-in users shouldn't see auth/landing screens — send them to their home surface.
  if ((to.name === 'login' || to.name === 'register' || to.name === 'welcome') && auth.isAuthenticated) {
    return { name: 'home' }
  }

  return true
})

export default router
