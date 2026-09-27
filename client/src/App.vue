<template>
  <div class="app">
    <aside class="sidebar">
      <div class="sidebar-header">
        <div class="logo">
          <h1>{{ t('nav.companyName') }}</h1>
          <span class="subtitle">{{ t('nav.subtitle') }}</span>
        </div>
      </div>

      <nav class="sidebar-nav">
        <router-link to="/" :class="{ active: $route.path === '/' }">
          <svg class="nav-icon" viewBox="0 0 20 20" fill="none"><path d="M3 8L10 2.5L17 8V16.5C17 17.0523 16.5523 17.5 16 17.5H12.5V12H7.5V17.5H4C3.44772 17.5 3 17.0523 3 16.5V8Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/></svg>
          <span>{{ t('nav.overview') }}</span>
        </router-link>
        <router-link to="/inventory" :class="{ active: $route.path === '/inventory' }">
          <svg class="nav-icon" viewBox="0 0 20 20" fill="none"><path d="M10 2L17.5 6V14L10 18L2.5 14V6L10 2Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/><path d="M2.5 6L10 10M10 10L17.5 6M10 10V18" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/></svg>
          <span>{{ t('nav.inventory') }}</span>
        </router-link>
        <router-link to="/orders" :class="{ active: $route.path === '/orders' }">
          <svg class="nav-icon" viewBox="0 0 20 20" fill="none"><rect x="4" y="3.5" width="12" height="15" rx="1.5" stroke="currentColor" stroke-width="1.5"/><path d="M7.5 3V2.5C7.5 1.94772 7.94772 1.5 8.5 1.5H11.5C12.0523 1.5 12.5 1.94772 12.5 2.5V3" stroke="currentColor" stroke-width="1.5"/><path d="M7 9H13M7 12.5H13M7 15.5H10.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          <span>{{ t('nav.orders') }}</span>
        </router-link>
        <router-link to="/restocking" :class="{ active: $route.path === '/restocking' }">
          <svg class="nav-icon" viewBox="0 0 20 20" fill="none"><path d="M17 10C17 13.866 13.866 17 10 17C7.5 17 5.29 15.67 4 13.7M3 10C3 6.13401 6.13401 3 10 3C12.5 3 14.71 4.33 16 6.3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><path d="M4 9V13.7H8.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M16 11V6.3H11.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
          <span>{{ t('nav.restocking') }}</span>
        </router-link>
        <router-link to="/spending" :class="{ active: $route.path === '/spending' }">
          <svg class="nav-icon" viewBox="0 0 20 20" fill="none"><path d="M10 2V18" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><path d="M13.5 5.5C13.5 5.5 12.2 4 10 4C8 4 6.5 5 6.5 6.5C6.5 9.5 13.5 8.5 13.5 12.5C13.5 14 12 15 10 15C7.8 15 6.5 13.5 6.5 13.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
          <span>{{ t('nav.finance') }}</span>
        </router-link>
        <router-link to="/demand" :class="{ active: $route.path === '/demand' }">
          <svg class="nav-icon" viewBox="0 0 20 20" fill="none"><path d="M2.5 14.5L8 9L11 12L17.5 5.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M13 5.5H17.5V10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
          <span>{{ t('nav.demandForecast') }}</span>
        </router-link>
        <router-link to="/reports" :class="{ active: $route.path === '/reports' }">
          <svg class="nav-icon" viewBox="0 0 20 20" fill="none"><path d="M3 17V3M3 17H17" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><rect x="6" y="10" width="2.5" height="5" fill="currentColor"/><rect x="10.5" y="7" width="2.5" height="8" fill="currentColor"/><rect x="13.5" y="5" width="2.5" height="10" fill="currentColor"/></svg>
          <span>{{ t('nav.reports') }}</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <LanguageSwitcher />
        <ProfileMenu
          @show-profile-details="showProfileDetails = true"
          @show-tasks="showTasks = true"
        />
      </div>
    </aside>

    <div class="main-column">
      <FilterBar />
      <main class="main-content">
        <router-view />
      </main>
    </div>

    <ProfileDetailsModal
      :is-open="showProfileDetails"
      @close="showProfileDetails = false"
    />

    <TasksModal
      :is-open="showTasks"
      :tasks="tasks"
      @close="showTasks = false"
      @add-task="addTask"
      @delete-task="deleteTask"
      @toggle-task="toggleTask"
    />
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import FilterBar from './components/FilterBar.vue'
import ProfileMenu from './components/ProfileMenu.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'
import LanguageSwitcher from './components/LanguageSwitcher.vue'

export default {
  name: 'App',
  components: {
    FilterBar,
    ProfileMenu,
    ProfileDetailsModal,
    TasksModal,
    LanguageSwitcher
  },
  setup() {
    const { currentUser } = useAuth()
    const { t } = useI18n()
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])

    // Merge mock tasks from currentUser with API tasks
    const tasks = computed(() => {
      return [...currentUser.value.tasks, ...apiTasks.value]
    })

    const loadTasks = async () => {
      try {
        apiTasks.value = await api.getTasks()
      } catch (err) {
        console.error('Failed to load tasks:', err)
      }
    }

    const addTask = async (taskData) => {
      try {
        const newTask = await api.createTask(taskData)
        // Add new task to the beginning of the array
        apiTasks.value.unshift(newTask)
      } catch (err) {
        console.error('Failed to add task:', err)
      }
    }

    const deleteTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const isMockTask = currentUser.value.tasks.some(t => t.id === taskId)

        if (isMockTask) {
          // Remove from mock tasks
          const index = currentUser.value.tasks.findIndex(t => t.id === taskId)
          if (index !== -1) {
            currentUser.value.tasks.splice(index, 1)
          }
        } else {
          // Remove from API tasks
          await api.deleteTask(taskId)
          apiTasks.value = apiTasks.value.filter(t => t.id !== taskId)
        }
      } catch (err) {
        console.error('Failed to delete task:', err)
      }
    }

    const toggleTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const mockTask = currentUser.value.tasks.find(t => t.id === taskId)

        if (mockTask) {
          // Toggle mock task status
          mockTask.status = mockTask.status === 'pending' ? 'completed' : 'pending'
        } else {
          // Toggle API task
          const updatedTask = await api.toggleTask(taskId)
          const index = apiTasks.value.findIndex(t => t.id === taskId)
          if (index !== -1) {
            apiTasks.value[index] = updatedTask
          }
        }
      } catch (err) {
        console.error('Failed to toggle task:', err)
      }
    }

    onMounted(loadTasks)

    return {
      t,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask
    }
  }
}
</script>

<style>
:root {
  /* Neutrals - dark navy surfaces */
  --color-background: #0b1120;
  --color-surface: #111a2e;
  --color-surface-alt: #1a2540;
  --color-border: #24304d;
  --color-text: #e2e8f0;
  --color-text-muted: #94a3b8;

  /* Accent - orange */
  --color-accent: #f97316;
  --color-accent-hover: #fb923c;
  --color-accent-subtle: rgba(249, 115, 22, 0.14);

  /* Semantic */
  --color-success: #22c55e;
  --color-success-subtle: rgba(34, 197, 94, 0.15);
  --color-warning: #eab308;
  --color-warning-subtle: rgba(234, 179, 8, 0.15);
  --color-danger: #ef4444;
  --color-danger-subtle: rgba(239, 68, 68, 0.15);
  --color-info: #38bdf8;
  --color-info-subtle: rgba(56, 189, 248, 0.15);

  /* Spacing (4px base) */
  --space-1: 4px; --space-2: 8px; --space-3: 12px; --space-4: 16px;
  --space-5: 24px; --space-6: 32px; --space-8: 48px; --space-10: 64px;

  /* Typography */
  --text-xs: 0.75rem; --text-sm: 0.875rem; --text-base: 1rem;
  --text-lg: 1.125rem; --text-xl: 1.5rem; --text-2xl: 2rem;
  --font-weight-normal: 400; --font-weight-medium: 500;
  --font-weight-semibold: 600; --font-weight-bold: 700;

  /* Radius/shadow */
  --radius-sm: 6px; --radius-md: 8px; --radius-lg: 12px;
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 1px 3px rgba(0, 0, 0, 0.4), 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-lg: 0 4px 6px -1px rgba(0, 0, 0, 0.4), 0 2px 4px -1px rgba(0, 0, 0, 0.3);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background: var(--color-background);
  color: var(--color-text);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.app {
  display: flex;
  min-height: 100vh;
  background: var(--color-background);
}

.sidebar {
  width: 260px;
  flex-shrink: 0;
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
  z-index: 100;
}

.sidebar-header {
  padding: 1.5rem 1.5rem 1.25rem;
  border-bottom: 1px solid var(--color-border);
}

.logo {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.logo h1 {
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.025em;
}

.subtitle {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  font-weight: 400;
}

.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 1rem 0.875rem;
}

.sidebar-nav a {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 0.875rem;
  color: var(--color-text-muted);
  text-decoration: none;
  font-weight: 500;
  font-size: 0.875rem;
  border-radius: var(--radius-md);
  transition: all 0.2s ease;
}

.sidebar-nav a .nav-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.sidebar-nav a:hover {
  color: var(--color-text);
  background: var(--color-surface-alt);
}

.sidebar-nav a.active {
  color: var(--color-accent);
  background: var(--color-accent-subtle);
}

.sidebar-footer {
  padding: 1rem 0.875rem 1.25rem;
  border-top: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.main-column {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  width: 100%;
  padding: 1.5rem 2rem;
}

.page-header {
  margin-bottom: 1.5rem;
}

.page-header h2 {
  font-size: 1.875rem;
  font-weight: 700;
  color: var(--color-text);
  margin-bottom: 0.375rem;
  letter-spacing: -0.025em;
}

.page-header p {
  color: var(--color-text-muted);
  font-size: 0.938rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.25rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  background: var(--color-surface);
  padding: 1.25rem;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  transition: all 0.2s ease;
}

.stat-card:hover {
  border-color: var(--color-accent);
  box-shadow: var(--shadow-md);
}

.stat-label {
  color: var(--color-text-muted);
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 0.625rem;
}

.stat-value {
  font-size: 2.25rem;
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.025em;
}

.stat-card.warning .stat-value {
  color: var(--color-warning);
}

.stat-card.success .stat-value {
  color: var(--color-success);
}

.stat-card.danger .stat-value {
  color: var(--color-danger);
}

.stat-card.info .stat-value {
  color: var(--color-info);
}

.card {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  padding: 1.25rem;
  border: 1px solid var(--color-border);
  margin-bottom: 1.25rem;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.875rem;
  border-bottom: 1px solid var(--color-border);
}

.card-title {
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.025em;
}

.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: var(--color-surface-alt);
  border-top: 1px solid var(--color-border);
  border-bottom: 1px solid var(--color-border);
}

th {
  text-align: left;
  padding: 0.5rem 0.75rem;
  font-weight: 600;
  color: var(--color-text-muted);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

td {
  padding: 0.5rem 0.75rem;
  border-top: 1px solid var(--color-border);
  color: var(--color-text);
  font-size: 0.875rem;
}

tbody tr {
  transition: background-color 0.15s ease;
}

tbody tr:hover {
  background: var(--color-surface-alt);
}

.badge {
  display: inline-block;
  padding: 0.313rem 0.75rem;
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.badge.success {
  background: var(--color-success-subtle);
  color: var(--color-success);
}

.badge.warning {
  background: var(--color-warning-subtle);
  color: var(--color-warning);
}

.badge.danger {
  background: var(--color-danger-subtle);
  color: var(--color-danger);
}

.badge.info {
  background: var(--color-info-subtle);
  color: var(--color-info);
}

.badge.increasing {
  background: var(--color-success-subtle);
  color: var(--color-success);
}

.badge.decreasing {
  background: var(--color-danger-subtle);
  color: var(--color-danger);
}

.badge.stable {
  background: var(--color-info-subtle);
  color: var(--color-info);
}

.badge.high {
  background: var(--color-danger-subtle);
  color: var(--color-danger);
}

.badge.medium {
  background: var(--color-warning-subtle);
  color: var(--color-warning);
}

.badge.low {
  background: var(--color-info-subtle);
  color: var(--color-info);
}

.loading {
  text-align: center;
  padding: 3rem;
  color: var(--color-text-muted);
  font-size: 0.938rem;
}

.error {
  background: var(--color-danger-subtle);
  border: 1px solid var(--color-danger);
  color: var(--color-danger);
  padding: 1rem;
  border-radius: var(--radius-md);
  margin: 1rem 0;
  font-size: 0.938rem;
}
</style>
