<script setup lang="ts">
interface Props {
  variant?: 'primary' | 'secondary'
  full?: boolean
  disabled?: boolean
  type?: 'button' | 'submit' | 'reset'
}

withDefaults(defineProps<Props>(), {
  variant: 'primary',
  full: false,
  disabled: false,
  type: 'button',
})

defineEmits<{
  (e: 'click', event: MouseEvent): void
}>()
</script>

<template>
  <button
    :type="type"
    :disabled="disabled"
    class="btn"
    :class="[variant, { full }]"
    @click="$emit('click', $event)"
  >
    <slot />
  </button>
</template>

<style scoped>
.btn {
  min-height: 46px;
  padding: 0 17px;
  border-radius: 15px;
  font-weight: 800;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition:
    opacity 0.2s,
    transform 0.1s;
  user-select: none;
  font-size: 14px;
}

.btn:active:not(:disabled) {
  transform: scale(0.98);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.primary {
  color: #fff;
  background: linear-gradient(135deg, var(--pink), var(--pink-gradient-end));
  box-shadow: var(--btn-shadow);
}

.secondary {
  color: var(--ink);
  background: #f4eeeb;
}

.full {
  width: 100%;
  display: flex;
}
</style>
