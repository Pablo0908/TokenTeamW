import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue'), meta: { public: true } },
  { path: '/register', name: 'register', component: () => import('@/views/RegisterView.vue'), meta: { public: true } },

  { path: '/', name: 'home', component: () => import('@/views/HomeView.vue'), meta: { requiresAuth: true } },
  { path: '/scan', name: 'scan', component: () => import('@/views/ScanView.vue'), meta: { requiresAuth: true } },
  { path: '/badges', name: 'badges', component: () => import('@/views/BadgesView.vue'), meta: { requiresAuth: true } },
  { path: '/events', name: 'events', component: () => import('@/views/EventsView.vue'), meta: { requiresAuth: true } },
  { path: '/events/:id', name: 'event-detail', component: () => import('@/views/EventDetailView.vue'), meta: { requiresAuth: true } },
  { path: '/profile', name: 'profile', component: () => import('@/views/ProfileView.vue'), meta: { requiresAuth: true } },

  // Public QR landing — redirects to login then back (handled inside the view).
  { path: '/redeem/:eventId/:token', name: 'redeem', component: () => import('@/views/RedeemView.vue'), meta: { public: true } },

  { path: '/admin/events', name: 'admin-events', component: () => import('@/views/admin/AdminEventsView.vue'), meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/admin/users', name: 'admin-users', component: () => import('@/views/admin/AdminUsersView.vue'), meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/admin/events/new', name: 'admin-event-new', component: () => import('@/views/admin/AdminEventNewView.vue'), meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/admin/events/:id', name: 'admin-event-detail', component: () => import('@/views/admin/AdminEventDetailView.vue'), meta: { requiresAuth: true, requiresAdmin: true } },

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
    return { name: 'login' }
  }

  if (to.meta.requiresAdmin && !auth.isAdmin) {
    return { name: 'home' }
  }

  // Logged-in users shouldn't see auth screens — send them to their home surface.
  if ((to.name === 'login' || to.name === 'register') && auth.isAuthenticated) {
    return auth.isAdmin ? { name: 'admin-events' } : { name: 'home' }
  }

  return true
})

export default router
