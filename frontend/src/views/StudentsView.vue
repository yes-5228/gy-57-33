<template>
  <section class="view">
    <header class="view-header">
      <div>
        <p class="eyebrow">Student</p>
        <h2>学员管理</h2>
      </div>
    </header>

    <div class="split">
      <form class="panel form" @submit.prevent="submit">
        <h3>新增学员</h3>
        <label>姓名<input v-model="form.name" required /></label>
        <label>电话<input v-model="form.phone" required /></label>
        <label>剩余课时<input v-model.number="form.remaining_hours" type="number" min="0" required /></label>
        <button class="primary" type="submit">
          <UserPlus :size="18" />
          保存学员
        </button>
      </form>

      <section class="panel list-panel">
        <h3>学员列表</h3>
        <table>
          <thead>
            <tr>
              <th>姓名</th>
              <th>电话</th>
              <th>剩余课时</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="student in students" :key="student.id">
              <td>{{ student.name }}</td>
              <td>{{ student.phone }}</td>
              <td>{{ student.remaining_hours }}h</td>
            </tr>
          </tbody>
        </table>
      </section>
    </div>
  </section>
</template>

<script setup>
import { reactive } from 'vue'
import { UserPlus } from 'lucide-vue-next'
import { studentApi } from '../api/modules'

defineProps({
  students: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['changed'])
const form = reactive({
  name: '',
  phone: '',
  remaining_hours: 20,
})

async function submit() {
  await studentApi.create(form)
  form.name = ''
  form.phone = ''
  form.remaining_hours = 20
  emit('changed')
}
</script>
