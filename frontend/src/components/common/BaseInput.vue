<script setup lang="ts">
interface Props {
  modelValue: string
  id?: string
  type?: string
  label?: string
  placeholder?: string
  maxlength?: number
  inputmode?: 'none' | 'text' | 'decimal' | 'numeric' | 'tel' | 'search' | 'email' | 'url'
}

withDefaults(defineProps<Props>(), {
  type: 'text',
})

defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()
</script>

<template>
  <div class="field">
    <label v-if="label" :for="id">{{ label }}</label>
    <input
      :id="id"
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :maxlength="maxlength"
      :inputmode="inputmode"
      @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
    />
  </div>
</template>

<style scoped>
.field {
  margin-top: 15px;
  width: 100%;
}

label {
  display: block;
  margin: 0 0 7px 3px;
  font-size: 12px;
  font-weight: 800;
  color: var(--ink);
}

input {
  width: 100%;
  height: 49px;
  padding: 0 14px;
  border: 1px solid var(--line);
  border-radius: 14px;
  outline: 0;
  background: #fffdfa;
  transition:
    border-color 0.2s,
    box-shadow 0.2s;
  color: var(--ink);
}

input:focus {
  border-color: var(--pink);
  box-shadow: 0 0 0 4px rgba(255, 130, 149, 0.11);
}

input::placeholder {
  color: var(--muted);
  opacity: 0.6;
}
</style>
