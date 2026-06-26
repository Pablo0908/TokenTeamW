import { t } from '@/i18n'

// Maps backend enum values to localized labels. Mirrors the rarity.js pattern:
// look up the i18n key, but fall back to the raw value if the key is missing so
// the UI never shows a literal dot-path (same guard auditActionLabel uses).
function labeled(prefix, value) {
  if (!value) return ''
  const key = `${prefix}.${value}`
  const label = t(key)
  return label === key ? value : label
}

// Organization member roles: owner | admin | staff.
export const roleLabel = (role) => labeled('org.roles', role)

// Event types: conference | workshop | meetup | hackathon | networking | other.
export const eventTypeLabel = (type) => labeled('eventTypes', type)

// Invite lifecycle: pending | revoked | accepted.
export const inviteStatusLabel = (status) => labeled('org.inviteStatus', status)

// Platform user roles: attendee | assistant | admin. Reuses the existing
// admin.users.role* keys (camelCase suffix), so it maps e.g. 'attendee' →
// 'admin.users.roleAttendee'. Falls back to the raw value if unmapped.
export const userRoleLabel = (role) => {
  if (!role) return ''
  const key = `admin.users.role${role.charAt(0).toUpperCase()}${role.slice(1)}`
  const label = t(key)
  return label === key ? role : label
}
