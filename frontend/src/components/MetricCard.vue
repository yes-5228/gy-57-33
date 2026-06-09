<template>
  <article class="metric">
    <p>{{ label }}</p>
    <strong>{{ value }}</strong>
  </article>
</template>

<script setup>
defineProps({
  label: {
    type: String,
    required: true,
  },
  value: {
    type: [String, Number],
    required: true,
  },
})
</script>
