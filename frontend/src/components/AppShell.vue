<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div>
        <p class="eyebrow">Drive School</p>
        <h1>驾校约车系统</h1>
      </div>
      <nav class="nav">
        <button
          v-for="item in items"
          :key="item.key"
          :class="{ active: modelValue === item.key }"
          @click="$emit('update:modelValue', item.key)"
        >
          <component :is="item.icon" :size="18" />
          <span>{{ item.label }}</span>
        </button>
      </nav>
    </aside>
    <main class="content">
      <slot />
    </main>
  </div>
</template>

<script setup>
import { CalendarDays, ClipboardList, Gauge, UserRoundCog, UsersRound } from 'lucide-vue-next'

defineProps({
  modelValue: {
    type: String,
    required: true,
  },
})

defineEmits(['update:modelValue'])

const items = [
  { key: 'dashboard', label: '概览', icon: Gauge },
  { key: 'appointments', label: '预约', icon: CalendarDays },
  { key: 'coaches', label: '教练', icon: UserRoundCog },
  { key: 'students', label: '学员', icon: UsersRound },
  { key: 'stats', label: '课时统计', icon: ClipboardList },
]
</script>
