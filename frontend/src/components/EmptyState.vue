<template>
  <div class="empty-state">{{ text }}</div>
</template>

<script setup>
defineProps({
  text: {
    type: String,
    default: '暂无数据',
  },
})
</script>
