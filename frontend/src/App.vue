<script setup>
import { ref, onMounted } from 'vue'
import LifetimeCalendar from './components/LifetimeCalendar.vue'
import UserSettings from './components/UserSettings.vue'
import axios from 'axios'

const API_BASE = 'http://localhost:8000'

const userData = ref(null)
const showSettings = ref(false)
const isLoading = ref(true)
const darkMode = ref(false)

// Theme management
const initTheme = () => {
  const savedTheme = localStorage.getItem('lifetime-calendar-theme')
  
  if (savedTheme && (savedTheme === 'dark' || savedTheme === 'light')) {
    // Use saved preference
    darkMode.value = savedTheme === 'dark'
    updateTheme()
  } else {
    // Use system preference and save it
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    darkMode.value = prefersDark
    localStorage.setItem('lifetime-calendar-theme', prefersDark ? 'dark' : 'light')
    updateTheme()
  }
}

const toggleTheme = () => {
  darkMode.value = !darkMode.value
  const newTheme = darkMode.value ? 'dark' : 'light'
  localStorage.setItem('lifetime-calendar-theme', newTheme)
  updateTheme()
}

const updateTheme = () => {
  const theme = darkMode.value ? 'dark' : 'light'
  document.documentElement.setAttribute('data-theme', theme)
  
  // Also update meta theme-color for better mobile experience
  let metaThemeColor = document.querySelector('meta[name="theme-color"]')
  if (!metaThemeColor) {
    metaThemeColor = document.createElement('meta')
    metaThemeColor.name = 'theme-color'
    document.head.appendChild(metaThemeColor)
  }
  metaThemeColor.content = darkMode.value ? '#0a0a0a' : '#f0f9ff'
}

const loadUserData = async () => {
  try {
    isLoading.value = true
    const response = await axios.get(`${API_BASE}/api/user`)
    userData.value = response.data
    if (!userData.value) {
      showSettings.value = true
    }
  } catch (error) {
    console.error('Error loading user data:', error)
    showSettings.value = true
  } finally {
    isLoading.value = false
  }
}

const handleUserSaved = (newUserData) => {
  userData.value = newUserData
  showSettings.value = false
}

const openSettings = () => {
  showSettings.value = true
}

// Listen for system theme changes when no manual preference is set
const handleSystemThemeChange = (e) => {
  const savedTheme = localStorage.getItem('lifetime-calendar-theme')
  // Only respond to system changes if user hasn't manually set a preference
  if (!savedTheme || savedTheme === 'system') {
    darkMode.value = e.matches
    updateTheme()
  }
}

onMounted(() => {
  initTheme()
  loadUserData()
  
  // Listen for system theme changes
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
  mediaQuery.addEventListener('change', handleSystemThemeChange)
  
  // Cleanup listener on unmount
  const cleanup = () => {
    mediaQuery.removeEventListener('change', handleSystemThemeChange)
  }
  
  // Store cleanup function for potential use
  window.addEventListener('beforeunload', cleanup)
})
</script>

<template>
  <div id="app">
    <header class="header">
      <div class="header-content">
        <div class="header-text">
          <h1 class="header-title">
            <span class="header-icon">🗓️</span>
            Lifetime Calendar
          </h1>
          <p class="header-subtitle">Track every week of your life</p>
        </div>
        
        <div class="header-controls">
          <button 
            class="theme-toggle-btn" 
            @click="toggleTheme"
            :aria-label="darkMode ? 'Switch to light mode' : 'Switch to dark mode'"
            :title="darkMode ? 'Switch to light mode' : 'Switch to dark mode'"
          >
            <span class="theme-icon">{{ darkMode ? '☀️' : '🌙' }}</span>
          </button>
          
          <button 
            class="settings-btn" 
            @click="openSettings"
            :disabled="isLoading"
            aria-label="Open settings"
            title="Open settings"
          >
            <span class="settings-icon">⚙️</span>
            <span class="settings-text">Settings</span>
          </button>
        </div>
      </div>
    </header>

    <main class="main">
      <!-- Loading State -->
      <div v-if="isLoading" class="loading-container">
        <div class="skeleton-stats">
          <div class="skeleton-card" v-for="i in 4" :key="i">
            <div class="skeleton-value"></div>
            <div class="skeleton-label"></div>
          </div>
        </div>
        <div class="skeleton-legend">
          <div class="skeleton-legend-item" v-for="i in 5" :key="i">
            <div class="skeleton-indicator"></div>
            <div class="skeleton-text"></div>
          </div>
        </div>
        <div class="skeleton-calendar">
          <div class="skeleton-grid">
            <div class="skeleton-week" v-for="i in 260" :key="i"></div>
          </div>
        </div>
      </div>
      
      <!-- Settings View -->
      <UserSettings 
        v-else-if="showSettings"
        :user-data="userData"
        @user-saved="handleUserSaved"
        @close="showSettings = false"
      />
      
      <!-- Calendar View -->
      <LifetimeCalendar 
        v-else-if="userData"
        :user-data="userData"
      />
    </main>
  </div>
</template>

<style scoped>
/* Header Styles */
.header {
  background: linear-gradient(135deg, var(--color-primary-600) 0%, var(--color-primary-800) 100%);
  color: var(--color-text-inverse);
  padding: var(--space-8) var(--space-6);
  position: relative;
  overflow: hidden;
}

.header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(circle at 20% 80%, rgba(255, 255, 255, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(255, 255, 255, 0.1) 0%, transparent 50%);
  pointer-events: none;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  z-index: 1;
}

.header-text {
  text-align: left;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.theme-toggle-btn {
  background: var(--glass-bg);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  border: 1px solid var(--glass-border);
  color: var(--color-text-inverse);
  padding: var(--space-3);
  border-radius: var(--radius-full);
  cursor: pointer;
  font-size: var(--font-size-lg);
  transition: var(--duration-normal) var(--ease-out);
  transition-property: transform, background-color, box-shadow;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
}

.theme-toggle-btn:hover:not(:disabled) {
  transform: translateY(-1px) scale(1.05);
  background: rgba(255, 255, 255, 0.2);
  box-shadow: var(--shadow-lg);
}

.theme-toggle-btn:active:not(:disabled) {
  transform: translateY(0) scale(1);
}

.theme-icon {
  font-size: var(--font-size-lg);
  transition: var(--duration-normal) var(--ease-out);
}

.header-title {
  font-size: var(--font-size-4xl);
  font-weight: var(--font-weight-bold);
  margin-bottom: var(--space-2);
  display: flex;
  align-items: center;
  gap: var(--space-3);
  line-height: var(--line-height-tight);
}

.header-icon {
  font-size: var(--font-size-3xl);
  animation: subtle-bounce 3s ease-in-out infinite;
}

@keyframes subtle-bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-2px); }
}

.header-subtitle {
  font-size: var(--font-size-lg);
  opacity: 0.9;
  font-weight: var(--font-weight-normal);
  margin: 0;
}

.settings-btn {
  background: var(--glass-bg);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  border: 1px solid var(--glass-border);
  color: var(--color-text-inverse);
  padding: var(--space-3) var(--space-5);
  border-radius: var(--radius-2xl);
  cursor: pointer;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  transition: var(--duration-normal) var(--ease-out);
  transition-property: transform, background-color, box-shadow;
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.settings-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  background: rgba(255, 255, 255, 0.2);
  box-shadow: var(--shadow-lg);
}

.settings-btn:active:not(:disabled) {
  transform: translateY(0);
}

.settings-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.settings-icon {
  font-size: var(--font-size-base);
}

.settings-text {
  display: none;
}

/* Main Content */
.main {
  flex: 1;
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--space-6);
  width: 100%;
}

/* Loading State */
.loading-container {
  padding: var(--space-6);
  animation: fadeIn var(--duration-slow) var(--ease-out);
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Skeleton Loading */
.skeleton-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--space-4);
  margin-bottom: var(--space-8);
}

.skeleton-card {
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  padding: var(--space-6);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--color-border);
}

.skeleton-value {
  height: 2.5rem;
  background: var(--color-background-secondary);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-3);
  animation: shimmer 2s infinite;
}

.skeleton-label {
  height: 1rem;
  width: 60%;
  background: var(--color-background-secondary);
  border-radius: var(--radius-sm);
  animation: shimmer 2s infinite;
  animation-delay: 0.2s;
}

.skeleton-legend {
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  padding: var(--space-6);
  margin-bottom: var(--space-6);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--color-border);
}

.skeleton-legend-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-3);
}

.skeleton-legend-item:last-child {
  margin-bottom: 0;
}

.skeleton-indicator {
  width: 16px;
  height: 16px;
  background: var(--color-background-secondary);
  border-radius: var(--radius-sm);
  animation: shimmer 2s infinite;
}

.skeleton-text {
  height: 1rem;
  width: 80px;
  background: var(--color-background-secondary);
  border-radius: var(--radius-sm);
  animation: shimmer 2s infinite;
  animation-delay: 0.1s;
}

.skeleton-calendar {
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  padding: var(--space-6);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--color-border);
}

.skeleton-grid {
  display: grid;
  grid-template-columns: repeat(52, 1fr);
  gap: 2px;
  max-width: 100%;
}

.skeleton-week {
  aspect-ratio: 1;
  background: var(--color-background-secondary);
  border-radius: 2px;
  animation: shimmer 2s infinite;
}

.skeleton-week:nth-child(3n) {
  animation-delay: 0.1s;
}

.skeleton-week:nth-child(5n) {
  animation-delay: 0.2s;
}

@keyframes shimmer {
  0% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
  100% {
    opacity: 1;
  }
}

/* Responsive Design */
@media (max-width: 768px) {
  .header {
    padding: var(--space-6) var(--space-4);
  }
  
  .header-content {
    flex-direction: column;
    gap: var(--space-4);
    text-align: center;
  }
  
  .header-text {
    text-align: center;
  }
  
  .header-controls {
    justify-content: center;
  }
  
  .header-title {
    font-size: var(--font-size-3xl);
    justify-content: center;
  }
  
  .settings-btn {
    padding: var(--space-3) var(--space-6);
  }
  
  .settings-text {
    display: inline;
  }
  
  .main {
    padding: var(--space-4);
  }
  
  .skeleton-stats {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .skeleton-grid {
    grid-template-columns: repeat(26, 1fr);
  }
}

@media (max-width: 480px) {
  .header-title {
    font-size: var(--font-size-2xl);
    flex-direction: column;
    gap: var(--space-2);
  }
  
  .header-subtitle {
    font-size: var(--font-size-base);
  }
  
  .header-controls {
    flex-direction: row;
    gap: var(--space-2);
  }
  
  .theme-toggle-btn {
    width: 40px;
    height: 40px;
    font-size: var(--font-size-base);
  }
  
  .settings-btn {
    padding: var(--space-2) var(--space-4);
    font-size: var(--font-size-sm);
  }
  
  .skeleton-stats {
    grid-template-columns: 1fr;
  }
  
  .skeleton-grid {
    grid-template-columns: repeat(13, 1fr);
  }
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  .header-icon {
    animation: none;
  }
  
  .theme-toggle-btn {
    transition: none;
  }
  
  .settings-btn {
    transition: none;
  }
  
  .skeleton-value,
  .skeleton-label,
  .skeleton-indicator,
  .skeleton-text,
  .skeleton-week {
    animation: none;
  }
  
  .loading-container {
    animation: none;
  }
}
</style>