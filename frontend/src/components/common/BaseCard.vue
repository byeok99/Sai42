<script setup lang="ts">
// Basic card wrapper
</script>

<template>
  <div class="card">
    <slot />
  </div>
</template>

<style scoped>
.card {
  background: #fff;
  border-radius: 21px;
  box-shadow: var(--shadow);
  overflow: hidden;
}
</style>
