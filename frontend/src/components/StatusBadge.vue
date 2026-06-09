<template>
  <span class="badge" :class="status">{{ labels[status] || status }}</span>
</template>

<script setup>
defineProps({
  status: {
    type: String,
    required: true,
  },
})

const labels = {
  booked: '已预约',
  cancelled: '已取消',
  completed: '已完成',
}
</script>
