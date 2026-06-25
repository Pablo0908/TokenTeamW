<script setup>
import { reactive, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useEventsStore } from '@/stores/events'
import AlertMessage from '@/components/ui/AlertMessage.vue'
import { t } from '@/i18n'
import { eventTypeLabel } from '@/utils/labels'

const router = useRouter()
const events = useEventsStore()

const form = reactive({ name: '', description: '', event_type: 'conference', visibility: 'public', date: '', end_date: '', location: '', prize: '' })
const touched = ref(false)
const submitting = ref(false)

const EVENT_TYPES = ['conference', 'workshop', 'meetup', 'hackathon', 'networking', 'other']
const VISIBILITIES = computed(() => [
  { value: 'public', label: t('admin.eventNew.visPublic') },
  { value: 'unlisted', label: t('admin.eventNew.visUnlisted') },
  { value: 'scan-only', label: t('admin.eventNew.visScanOnly') },
])

const valid = computed(() => form.name.trim().length > 0)

async function submit() {
  touched.value = true
  if (!valid.value) return
  submitting.value = true
  try {
    const created = await events.createEvent({ ...form, name: form.name.trim() })
    events.loaded = false // list should refetch to include the new event
    router.push(`/admin/events/${created.id}`)
  } catch {
    /* error surfaced via store */
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="space-y-5 px-4 pb-10 pt-6">
    <button class="tap-target -ml-1 flex items-center gap-1 text-sm text-base-content/70" @click="router.back()">
      <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M15 19l-7-7 7-7" />
      </svg>
      {{ $t('admin.eventNew.back') }}
    </button>

    <header>
      <h1 class="text-2xl font-bold">{{ $t('admin.eventNew.title') }}</h1>
      <p class="text-sm text-base-content/60">{{ $t('admin.eventNew.subtitle') }}</p>
    </header>

    <form class="space-y-4" novalidate @submit.prevent="submit">
      <AlertMessage type="error" :message="events.error || ''" />

      <label class="form-control w-full">
        <span class="label-text mb-1 text-base-content/70">{{ $t('admin.eventNew.nameLabel') }}</span>
        <input
          v-model="form.name"
          type="text"
          class="input input-bordered w-full bg-base-100/70"
          :class="{ 'input-error': touched && !valid }"
          :placeholder="$t('admin.eventNew.namePlaceholder')"
        />
        <span v-if="touched && !valid" class="mt-1 text-xs text-error">{{ $t('admin.eventNew.nameRequired') }}</span>
      </label>

      <label class="form-control w-full">
        <span class="label-text mb-1 text-base-content/70">{{ $t('admin.eventNew.descriptionLabel') }}</span>
        <textarea
          v-model="form.description"
          rows="3"
          class="textarea textarea-bordered w-full bg-base-100/70"
          :placeholder="$t('admin.eventNew.descriptionPlaceholder')"
        />
      </label>

      <label class="form-control w-full">
        <span class="label-text mb-1 text-base-content/70">{{ $t('admin.eventNew.typeLabel') }}</span>
        <select v-model="form.event_type" class="select select-bordered w-full bg-base-100/70">
          <option v-for="ty in EVENT_TYPES" :key="ty" :value="ty">{{ eventTypeLabel(ty) }}</option>
        </select>
      </label>

      <label class="form-control w-full">
        <span class="label-text mb-1 text-base-content/70">{{ $t('admin.eventNew.visibilityLabel') }}</span>
        <select v-model="form.visibility" class="select select-bordered w-full bg-base-100/70">
          <option v-for="v in VISIBILITIES" :key="v.value" :value="v.value">{{ v.label }}</option>
        </select>
      </label>

      <div class="flex gap-3">
        <label class="form-control flex-1">
          <span class="label-text mb-1 text-base-content/70">{{ $t('admin.eventNew.startDate') }}</span>
          <input v-model="form.date" type="date" class="input input-bordered w-full bg-base-100/70" />
        </label>
        <label class="form-control flex-1">
          <span class="label-text mb-1 text-base-content/70">{{ $t('admin.eventNew.endDate') }}</span>
          <input v-model="form.end_date" type="date" class="input input-bordered w-full bg-base-100/70" />
        </label>
      </div>

      <label class="form-control w-full">
        <span class="label-text mb-1 text-base-content/70">{{ $t('admin.eventNew.locationLabel') }}</span>
        <input v-model="form.location" type="text" class="input input-bordered w-full bg-base-100/70" :placeholder="$t('admin.eventNew.locationPlaceholder')" />
      </label>

      <label class="form-control w-full">
        <span class="label-text mb-1 text-base-content/70">{{ $t('admin.eventNew.prizeLabel') }}</span>
        <input v-model="form.prize" type="text" class="input input-bordered w-full bg-base-100/70" :placeholder="$t('admin.eventNew.prizePlaceholder')" />
      </label>

      <!-- eslint-disable-next-line vue/no-v-html -->
      <p class="text-xs text-base-content/55" v-html="$t('admin.eventNew.startsClosed')" />
      <button type="submit" class="btn btn-primary w-full tap-target" :disabled="submitting">
        <span v-if="submitting" class="loading loading-spinner loading-sm" />
        {{ submitting ? $t('admin.eventNew.creating') : $t('admin.eventNew.create') }}
      </button>
    </form>
  </div>
</template>
