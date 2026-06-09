<template>
  <section class="view">
    <header class="view-header">
      <div>
        <p class="eyebrow">Coach</p>
        <h2>教练管理</h2>
      </div>
    </header>

    <div class="split">
      <form class="panel form" @submit.prevent="submit">
        <h3>新增教练</h3>
        <label>姓名<input v-model="form.name" required /></label>
        <label>电话<input v-model="form.phone" required /></label>
        <label>车牌<input v-model="form.car_no" required /></label>
        <label>擅长项目<input v-model="specialtiesText" placeholder="科目二, 科目三" /></label>
        <button class="primary" type="submit">
          <UserPlus :size="18" />
          保存教练
        </button>
      </form>

      <section class="panel list-panel">
        <h3>教练列表</h3>
        <table>
          <thead>
            <tr>
              <th>教练</th>
              <th>车辆</th>
              <th>项目</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="coach in coaches" :key="coach.id">
              <td>{{ coach.name }}<br /><small>{{ coach.phone }}</small></td>
              <td>{{ coach.car_no }}</td>
              <td>{{ coach.specialties.join('、') || '-' }}</td>
              <td>{{ coach.active ? '在岗' : '停用' }}</td>
              <td>
                <button class="ghost" @click="toggle(coach)">
                  <Power :size="16" />
                  {{ coach.active ? '停用' : '启用' }}
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
import { reactive, ref } from 'vue'
import { Power, UserPlus } from 'lucide-vue-next'
import { coachApi } from '../api/modules'

defineProps({
  coaches: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['changed'])
const specialtiesText = ref('')
const form = reactive({
  name: '',
  phone: '',
  car_no: '',
})

async function submit() {
  await coachApi.create({
    ...form,
    specialties: specialtiesText.value.split(',').map((item) => item.trim()).filter(Boolean),
    active: true,
  })
  form.name = ''
  form.phone = ''
  form.car_no = ''
  specialtiesText.value = ''
  emit('changed')
}

async function toggle(coach) {
  await coachApi.setActive(coach.id, !coach.active)
  emit('changed')
}
</script>
