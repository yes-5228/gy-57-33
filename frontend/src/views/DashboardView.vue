<template>
  <section class="view">
    <header class="view-header">
      <div>
        <p class="eyebrow">Overview</p>
        <h2>运营概览</h2>
      </div>
      <button class="primary" @click="$emit('navigate', 'appointments')">
        <CalendarPlus :size="18" />
        新增预约
      </button>
    </header>

    <div class="metrics">
      <MetricCard label="学员数" :value="summary.total_students ?? '-'" />
      <MetricCard label="教练数" :value="summary.total_coaches ?? '-'" />
      <MetricCard label="进行中预约" :value="summary.active_bookings ?? '-'" />
      <MetricCard label="已完成课时" :value="summary.completed_hours ?? '-'" />
    </div>

    <section class="panel">
      <h3>取消规则</h3>
      <div class="rule-grid">
        <div>
          <span>提前取消</span>
          <strong>{{ summary.cancel_rule?.min_hours_before_start ?? '-' }} 小时</strong>
        </div>
        <div>
          <span>单学员可预约</span>
          <strong>{{ summary.cancel_rule?.max_active_bookings_per_student ?? '-' }} 单</strong>
        </div>
        <div>
          <span>已完成可取消</span>
          <strong>{{ summary.cancel_rule?.allow_cancel_completed ? '是' : '否' }}</strong>
        </div>
      </div>
    </section>
  </section>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { CalendarPlus } from 'lucide-vue-next'
import MetricCard from '../components/MetricCard.vue'
import { dashboardApi } from '../api/modules'

const props = defineProps({
  refreshToken: {
    type: Number,
    default: 0,
  },
})

defineEmits(['navigate'])

const summary = ref({})

async function load() {
  summary.value = await dashboardApi.summary()
}

onMounted(load)
watch(() => props.refreshToken, load)
</script>
