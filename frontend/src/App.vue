<template>
  <AppShell v-model="activeView">
    <DashboardView
      v-if="activeView === 'dashboard'"
      :refresh-token="refreshToken"
      @navigate="activeView = $event"
    />
    <AppointmentsView
      v-else-if="activeView === 'appointments'"
      :students="students"
      :coaches="coaches"
      :refresh-token="refreshToken"
      @changed="refreshAll"
    />
    <CoachesView
      v-else-if="activeView === 'coaches'"
      :coaches="coaches"
      @changed="refreshAll"
    />
    <StudentsView
      v-else-if="activeView === 'students'"
      :students="students"
      @changed="refreshAll"
    />
    <StatsView v-else :refresh-token="refreshToken" />
  </AppShell>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import AppShell from './components/AppShell.vue'
import AppointmentsView from './views/AppointmentsView.vue'
import CoachesView from './views/CoachesView.vue'
import DashboardView from './views/DashboardView.vue'
import StatsView from './views/StatsView.vue'
import StudentsView from './views/StudentsView.vue'
import { coachApi, studentApi } from './api/modules'

const activeView = ref('dashboard')
const students = ref([])
const coaches = ref([])
const refreshToken = ref(0)

async function refreshAll() {
  const [studentList, coachList] = await Promise.all([studentApi.list(), coachApi.list()])
  students.value = studentList
  coaches.value = coachList
  refreshToken.value += 1
}

onMounted(refreshAll)
</script>
