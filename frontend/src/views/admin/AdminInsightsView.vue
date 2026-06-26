<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { t } from '@/i18n'
import { eventTypeLabel } from '@/utils/labels'
import { api, readApiError } from '@/services/api'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import AlertMessage from '@/components/ui/AlertMessage.vue'
import StatTile from '@/components/domain/StatTile.vue'
import ActivityChart from '@/components/domain/ActivityChart.vue'
import DateRangePicker from '@/components/domain/DateRangePicker.vue'

const router = useRouter()

const data = ref(null)
const loading = ref(false)
const error = ref('')
const range = ref({ period: 'day', start: '', end: '' })

async function load() {
  loading.value = true; error.value = ''
  try {
    const { data: d } = await api.get('/admin/insights', { params: range.value })
    data.value = d
  } catch (e) { error.value = readApiError(e, t('admin.insights.couldNotLoad')) }
  finally { loading.value = false }
}
function onRange(r) { range.value = r; load() }

const userSeries = computed(() => [
  { label: t('admin.insights.activeUsers'), colorClass: 'bg-primary/70', data: data.value?.active_users ?? [] },
  { label: t('admin.insights.newUsers'), colorClass: 'bg-secondary/70', data: data.value?.user_growth ?? [] },
])
const mix = computed(() => data.value?.event_type_mix ?? [])
const mixMax = computed(() => mix.value.reduce((m, x) => Math.max(m, x.count), 0))
</script>

<template>
  <div class="space-y-5">
    <DateRangePicker @change="onRange" />

    <AlertMessage type="warning" :message="error" />
    <LoadingSpinner v-if="loading && !data" :label="$t('admin.loading')" />

    <template v-else-if="data">
      <div class="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatTile :value="data.totals.scans" :label="$t('admin.insights.totalScans')" tone="primary" />
        <StatTile :value="data.totals.users" :label="$t('admin.insights.totalUsers')" tone="secondary" />
        <StatTile :value="data.totals.events" :label="$t('admin.insights.totalEvents')" tone="accent" />
        <StatTile :value="data.totals.orgs" :label="$t('admin.insights.totalOrgs')" tone="primary" />
      </div>

      <div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div class="surface space-y-2 p-4">
          <h2 class="font-semibold">{{ $t('admin.insights.scansOverTime') }}</h2>
          <ActivityChart :activity="data.scans_over_time" :period="data.period" />
        </div>

        <div class="surface space-y-2 p-4">
          <div class="flex items-center justify-between">
            <h2 class="font-semibold">{{ $t('admin.insights.users') }}</h2>
            <span class="text-[0.65rem] text-base-content/45">{{ $t('admin.insights.usersNote') }}</span>
          </div>
          <ActivityChart :series="userSeries" :period="data.period" />
        </div>
      </div>

      <div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <div class="surface p-4">
        <h2 class="mb-2 font-semibold">{{ $t('admin.insights.topOrgs') }}</h2>
        <div v-if="data.org_leaderboard.length" class="space-y-1.5">
          <button
            v-for="o in data.org_leaderboard"
            :key="o.id"
            type="button"
            class="flex w-full items-center justify-between rounded-lg px-1 py-1.5 text-left hover:bg-base-100/60"
            @click="router.push('/admin/orgs')"
          >
            <span class="min-w-0 truncate text-sm">{{ o.name }}
              <span class="text-[0.7rem] text-base-content/45">· {{ $t('admin.insights.people', { n: o.participants }) }}</span>
            </span>
            <span class="shrink-0 text-sm font-semibold text-primary">{{ o.scans }} 🏅</span>
          </button>
        </div>
        <p v-else class="py-4 text-center text-sm text-base-content/50">{{ $t('admin.insights.noScansInRange') }}</p>
      </div>

      <div class="surface p-4">
        <h2 class="mb-2 font-semibold">{{ $t('admin.insights.eventTypes') }}</h2>
        <div v-if="mix.length" class="space-y-2">
          <div v-for="m in mix" :key="m.event_type">
            <div class="mb-0.5 flex justify-between text-xs">
              <span class="text-base-content/70">{{ eventTypeLabel(m.event_type) }}</span>
              <span class="text-base-content/50">{{ m.count }}</span>
            </div>
            <div class="h-2 overflow-hidden rounded-full bg-base-300/50">
              <div class="h-full rounded-full bg-primary/70" :style="{ width: `${mixMax ? (m.count / mixMax) * 100 : 0}%` }" />
            </div>
          </div>
        </div>
        <p v-else class="py-4 text-center text-sm text-base-content/50">{{ $t('admin.insights.noScansInRange') }}</p>
      </div>
      </div>
    </template>
  </div>
</template>
