import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useOrgContextStore } from '@/stores/orgContext'

const routes = [
  // Public marketing preview shown to logged-out visitors. The sign-in form lives at the
  // bottom of this page (scroll down), so unauthenticated users meet the preview first.
  { path: '/welcome', name: 'welcome', component: () => import('@/views/LandingView.vue'), meta: { public: true } },
  { path: '/forgot-password', name: 'forgot-password', component: () => import('@/views/ForgotPasswordView.vue'), meta: { public: true } },

  { path: '/', name: 'home', component: () => import('@/views/HomeView.vue'), meta: { requiresAuth: true } },
  { path: '/scan', name: 'scan', component: () => import('@/views/ScanView.vue'), meta: { requiresAuth: true } },
  { path: '/badges', name: 'badges', component: () => import('@/views/BadgesView.vue'), meta: { requiresAuth: true } },
  { path: '/events', name: 'events', component: () => import('@/views/EventsView.vue'), meta: { requiresAuth: true } },
  { path: '/events/:id', name: 'event-detail', component: () => import('@/views/EventDetailView.vue'), meta: { requiresAuth: true } },
  { path: '/profile', name: 'profile', component: () => import('@/views/ProfileView.vue'), meta: { requiresAuth: true } },
  { path: '/profile/settings', name: 'profile-settings', component: () => import('@/views/ProfileSettingsView.vue'), meta: { requiresAuth: true } },
  { path: '/profile/edit-name', name: 'profile-edit-name', component: () => import('@/views/ProfileEditNameView.vue'), meta: { requiresAuth: true } },
  { path: '/profile/change-password', name: 'profile-change-password', component: () => import('@/views/ProfileChangePasswordView.vue'), meta: { requiresAuth: true } },
  { path: '/profile/change-photo', name: 'profile-change-photo', component: () => import('@/views/ProfileChangePhotoView.vue'), meta: { requiresAuth: true } },
  { path: '/invites', name: 'invites', component: () => import('@/views/InvitesView.vue'), meta: { requiresAuth: true } },

  // Public QR landing — redirects to login then back (handled inside the view).
  { path: '/redeem/:eventId/:token', name: 'redeem', component: () => import('@/views/RedeemView.vue'), meta: { public: true } },

  // Platform panel — super-admin only (global events/users/audit across all orgs).
  // The tab pages are children of AdminLayout, which holds the persistent header + AdminNav
  // so the active-tab pill animates across navigations (matching the org panel, whose single
  // OrgPanelView component likewise persists its tabs). Title/eyebrow come from each route's meta.
  {
    path: '/admin',
    component: () => import('@/views/admin/AdminLayout.vue'),
    meta: { requiresAuth: true, requiresSuperAdmin: true },
    children: [
      { path: '', redirect: { name: 'admin-events' } },
      { path: 'events', name: 'admin-events', component: () => import('@/views/admin/AdminEventsView.vue'), meta: { eyebrow: 'roles.superAdmin', title: 'admin.eventsTitle' } },
      { path: 'users', name: 'admin-users', component: () => import('@/views/admin/AdminUsersView.vue'), meta: { eyebrow: 'roles.superAdmin', title: 'admin.users.title' } },
      { path: 'audit', name: 'admin-audit', component: () => import('@/views/admin/AdminAuditView.vue'), meta: { eyebrow: 'admin.organizer', title: 'admin.audit.title' } },
      { path: 'insights', name: 'admin-insights', component: () => import('@/views/admin/AdminInsightsView.vue'), meta: { eyebrow: 'admin.platform', title: 'admin.insights.title' } },
      { path: 'orgs', name: 'admin-orgs', component: () => import('@/views/admin/AdminOrgsView.vue'), meta: { eyebrow: 'admin.platform', title: 'admin.orgs.title' } },
      { path: 'org-invites', name: 'admin-org-invites', component: () => import('@/views/admin/AdminOrgInvitesView.vue'), meta: { eyebrow: 'admin.platform', title: 'admin.codes.title' } },
      { path: 'announcements', name: 'admin-announcements', component: () => import('@/views/admin/AdminAnnouncementsView.vue'), meta: { eyebrow: 'admin.platform', title: 'admin.announcements.title' } },
      { path: 'verifier', name: 'admin-verifier', component: () => import('@/views/admin/AdminVerifierView.vue'), meta: { eyebrow: 'admin.platform', title: 'verifier.title' } },
    ],
  },
  // Detail / create pages stand alone (no section nav).
  // /new must come before /:id so Vue Router doesn't treat "new" as an event ID.
  { path: '/admin/events/new', name: 'admin-event-new', component: () => import('@/views/admin/AdminEventNewView.vue'), meta: { requiresAuth: true, requiresSuperAdmin: true } },
  { path: '/admin/events/:id', name: 'admin-event-detail', component: () => import('@/views/admin/AdminEventDetailView.vue'), meta: { requiresAuth: true, requiresSuperAdmin: true } },
  { path: '/admin/users/:id', name: 'admin-user-detail', component: () => import('@/views/admin/AdminUserDetailView.vue'), meta: { requiresAuth: true, requiresSuperAdmin: true } },

  // Org-scoped panel — any member of the active org (tabs gate by role in-view).
  { path: '/org/:tab(dashboard|events|verifier|members|participants|audit|settings)?', name: 'org-panel', component: () => import('@/views/OrgPanelView.vue'), meta: { requiresAuth: true, requiresOrgMember: true } },
  // Org event detail — reuses the platform event-detail view in org-scoped mode
  // (same badge management: single, bulk, QR sheet) against the active org.
  { path: '/org/events/:id', name: 'org-event-detail', component: () => import('@/views/admin/AdminEventDetailView.vue'), meta: { requiresAuth: true, requiresOrgMember: true, orgScoped: true } },

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
    // Send logged-out users to the preview landing; its embedded sign-in form is one scroll away.
    return { name: 'welcome' }
  }

  // Logged-in users shouldn't see the preview or auth screens — send them to their home surface.
  if (to.name === 'welcome' && auth.isAuthenticated) {
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
