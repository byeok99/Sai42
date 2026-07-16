<script setup lang="ts">
defineProps<{
  eyebrow: string
  title: string
}>()
</script>

<template>
  <header class="page-header">
    <div class="page-heading">
      <span class="page-heading-mark" aria-hidden="true"></span>
      <div>
        <p>{{ eyebrow }}</p>
        <h2>{{ title }}</h2>
      </div>
    </div>
    <div class="page-header-action">
      <slot />
    </div>
  </header>
</template>

<style scoped>
.page-header {
  position: relative;
  z-index: 20;
  height: 72px;
  display: flex;
  flex: none;
  justify-content: space-between;
  align-items: center;
  padding: 12px 18px 10px;
  overflow: hidden;
  border-bottom: 1px solid rgba(238, 227, 224, 0.82);
  background:
    radial-gradient(circle at 87% -30%, rgba(221, 209, 255, 0.42), transparent 38%),
    rgba(255, 250, 245, 0.95);
  backdrop-filter: blur(12px);
}

.page-header::after {
  position: absolute;
  right: 18px;
  bottom: -1px;
  left: 18px;
  height: 1px;
  background: linear-gradient(90deg, rgba(255, 130, 149, 0.42), transparent 70%);
  content: '';
}

.page-heading {
  display: flex;
  align-items: center;
  gap: 10px;
}

.page-heading-mark {
  width: 5px;
  height: 36px;
  flex: none;
  border-radius: 999px;
  background: linear-gradient(180deg, var(--pink), #9e86dc);
  box-shadow: 0 5px 12px rgba(226, 95, 125, 0.22);
}

.page-heading p {
  margin: 0;
  color: #cf6178;
  font-size: 8px;
  font-weight: 900;
  letter-spacing: 0.14em;
}

.page-heading h2 {
  margin: 3px 0 0;
  color: var(--ink);
  font-size: 20px;
  font-weight: 900;
  letter-spacing: -0.03em;
}

.page-header-action {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
}
</style>
