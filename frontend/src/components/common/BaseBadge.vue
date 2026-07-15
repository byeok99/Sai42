<script setup lang="ts">
interface Props {
  variant?: 'default' | 'chip' | 'live' | 'time'
}

withDefaults(defineProps<Props>(), {
  variant: 'default',
})
</script>

<template>
  <span :class="['badge-base', variant]">
    <slot />
  </span>
</template>

<style scoped>
.badge-base {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
}

.default {
  padding: 7px 9px;
  border-radius: 11px;
  background: rgba(255, 255, 255, 0.7);
  font-size: 9px;
}

.chip {
  padding: 9px 11px;
  border-radius: 14px;
  background: #fff;
  box-shadow: var(--shadow);
  font-size: 11px;
  color: var(--ink);
}

.live {
  padding: 8px 10px;
  border-radius: 12px;
  background: #e4f6ee;
  color: #4e806c;
  font-size: 9px;
}

.time {
  padding: 7px 9px;
  border-radius: 11px;
  background: var(--yellow);
  font-size: 9px;
  color: var(--ink);
}
</style>
