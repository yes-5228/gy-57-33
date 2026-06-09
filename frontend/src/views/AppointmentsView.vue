<template>
  <section class="view">
    <header class="view-header">
      <div>
        <p class="eyebrow">Booking</p>
        <h2>练车预约</h2>
      </div>
    </header>

    <div class="split">
      <form class="panel form" @submit.prevent="submit">
        <h3>新建预约</h3>
        <label>
          学员
          <select v-model.number="form.student_id" required>
            <option value="" disabled>选择学员</option>
            <option v-for="student in students" :key="student.id" :value="student.id">
              {{ student.name }}（剩余 {{ student.remaining_hours }}h）
            </option>
          </select>
        </label>
        <label>
          教练
          <select v-model.number="form.coach_id" required>
            <option value="" disabled>选择教练</option>
            <option v-for="coach in activeCoaches" :key="coach.id" :value="coach.id">
              {{ coach.name }} - {{ coach.car_no }}
            </option>
          </select>
        </label>
        <label>
          开始时间
          <input v-model="form.start_time" type="datetime-local" required />
        </label>
        <label>
          结束时间
          <input v-model="form.end_time" type="datetime-local" required />
        </label>
        <button class="primary" type="submit">
          <CalendarCheck :size="18" />
          提交预约
        </button>
        <p v-if="message" class="message">{{ message }}</p>
      </form>

      <section class="panel list-panel">
        <h3>预约列表</h3>
        <EmptyState v-if="appointments.length === 0" />
        <table v-else>
          <thead>
            <tr>
              <th>时间</th>
              <th>学员</th>
              <th>教练</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in appointments" :key="item.id">
              <td>{{ formatDateTime(item.start_time) }} - {{ formatDateTime(item.end_time) }}</td>
              <td>{{ item.student_name }}</td>
              <td>{{ item.coach_name }}</td>
              <td><StatusBadge :status="item.status" /></td>
              <td>
                <button
                  class="ghost danger"
                  :disabled="item.status !== 'booked'"
                  @click="cancel(item.id)"
                >
                  <XCircle :size="16" />
                  取消
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </section>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { CalendarCheck, XCircle } from 'lucide-vue-next'
import EmptyState from '../components/EmptyState.vue'
import StatusBadge from '../components/StatusBadge.vue'
import { appointmentApi } from '../api/modules'
import { addHours, formatDateTime, toLocalInputValue } from '../utils/date'

const props = defineProps({
  students: {
    type: Array,
    default: () => [],
  },
  coaches: {
    type: Array,
    default: () => [],
  },
  refreshToken: {
    type: Number,
    default: 0,
  },
})

const emit = defineEmits(['changed'])

const appointments = ref([])
const message = ref('')
const initialStart = addHours(new Date(), 24)
const form = reactive({
  student_id: '',
  coach_id: '',
  start_time: toLocalInputValue(initialStart),
  end_time: toLocalInputValue(addHours(initialStart, 2)),
})

const activeCoaches = computed(() => props.coaches.filter((coach) => coach.active))

async function load() {
  appointments.value = await appointmentApi.list()
}

async function submit() {
  message.value = ''
  try {
    await appointmentApi.create({
      ...form,
      start_time: new Date(form.start_time).toISOString(),
      end_time: new Date(form.end_time).toISOString(),
    })
    message.value = '预约已创建'
    await load()
    emit('changed')
  } catch (error) {
    message.value = error.message
  }
}

async function cancel(id) {
  message.value = ''
  try {
    await appointmentApi.cancel(id, '前端操作取消')
    message.value = '预约已取消'
    await load()
    emit('changed')
  } catch (error) {
    message.value = error.message
  }
}

onMounted(load)
watch(() => props.refreshToken, load)
</script>
