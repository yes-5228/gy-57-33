<template>
  <section class="view">
    <header class="view-header">
      <div>
        <p class="eyebrow">Lesson</p>
        <h2>课时统计</h2>
      </div>
    </header>

    <section class="panel">
      <table>
        <thead>
          <tr>
            <th>学员</th>
            <th>已完成</th>
            <th>已预约</th>
            <th>取消次数</th>
            <th>剩余课时</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in stats" :key="item.student_id">
            <td>{{ item.student_name }}</td>
            <td>{{ item.completed_hours }}h</td>
            <td>{{ item.booked_hours }}h</td>
            <td>{{ item.cancelled_count }}</td>
            <td>{{ item.remaining_hours }}h</td>
          </tr>
        </tbody>
      </table>
    </section>
  </section>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { dashboardApi } from '../api/modules'

const props = defineProps({
  refreshToken: {
    type: Number,
    default: 0,
  },
})

const stats = ref([])

async function load() {
  stats.value = await dashboardApi.lessonStats()
}

onMounted(load)
watch(() => props.refreshToken, load)
</script>
