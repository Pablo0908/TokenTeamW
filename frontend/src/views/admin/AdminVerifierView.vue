<script setup>
import VerifierPanel from '@/components/domain/VerifierPanel.vue'

// Platform-wide prize verifier. The VerifierPanel is org-agnostic — the backend resolves the
// org from the scanned token; a super_admin may award any org's event.
</script>

<template>
  <div class="space-y-5">
    <div class="surface p-4">
      <VerifierPanel />
    </div>
  </div>
</template>
