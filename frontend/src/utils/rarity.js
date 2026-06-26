import { t } from '@/i18n'

// Rarity tiers mirror the backend (badge.rarity: legendary | epic | rare | common),
// derived from how few attendees have collected a badge. Static class strings so
// Tailwind's purge keeps them.
export const RARITY = {
  legendary: { emoji: '👑', dot: 'bg-warning', text: 'text-warning', ring: 'ring-warning/60' },
  epic: { emoji: '💎', dot: 'bg-secondary', text: 'text-secondary', ring: 'ring-secondary/60' },
  rare: { emoji: '⭐', dot: 'bg-info', text: 'text-info', ring: 'ring-info/60' },
  common: { emoji: '⚪', dot: 'bg-base-content/40', text: 'text-base-content/60', ring: 'ring-base-300' },
}

export const rarityMeta = (r) => RARITY[r] || null
export const rarityLabel = (r) => (RARITY[r] ? t(`rarity.${r}`) : '')
