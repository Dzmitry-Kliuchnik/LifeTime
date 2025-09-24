<script setup>
import { ref, onMounted } from 'vue'
import LifetimeCalendar from './components/LifetimeCalendar.vue'
import UserSettings from './components/UserSettings.vue'
import axios from 'axios'

const API_BASE = 'http://localhost:8000'

const userData = ref(null)
const showSettings = ref(false)

const loadUserData = async () => {
  try {
    const response = await axios.get(`${API_BASE}/api/user`)
    userData.value = response.data
    if (!userData.value) {
      showSettings.value = true
    }
  } catch (error) {
    console.error('Error loading user data:', error)
    showSettings.value = true
  }
}

const handleUserSaved = (newUserData) => {
  userData.value = newUserData
  showSettings.value = false
}

const openSettings = () => {
  showSettings.value = true
}

onMounted(() => {
  loadUserData()
})
</script>

<template>
  <div id="app">
    <header class="header">
      <h1>🗓️ Lifetime Calendar</h1>
      <p class="subtitle">Track every week of your life</p>
      <button class="settings-btn" @click="openSettings">⚙️ Settings</button>
    </header>

    <main class="main">
      <UserSettings 
        v-if="showSettings"
        :user-data="userData"
        @user-saved="handleUserSaved"
        @close="showSettings = false"
      />
      
      <LifetimeCalendar 
        v-else-if="userData"
        :user-data="userData"
      />
      
      <div v-else class="loading">
        Loading...
      </div>
    </main>
  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background: #f5f5f5;
  color: #333;
}

#app {
  min-height: 100vh;
}

.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 2rem 8rem 2rem 2rem;
  text-align: center;
  position: relative;
}

.header h1 {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
  font-weight: 700;
}

.subtitle {
  font-size: 1.2rem;
  opacity: 0.9;
  font-weight: 300;
}

.settings-btn {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s ease;
  margin-top: 1rem;
  display: block;
  margin-left: auto;
  margin-right: auto;
}

.settings-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
}

.main {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.loading {
  text-align: center;
  font-size: 1.2rem;
  color: #666;
  padding: 4rem;
}

@media (max-width: 768px) {
  .header {
    padding: 2rem 1rem;
  }
  
  .header h1 {
    font-size: 2rem;
  }
  
  .settings-btn {
    margin-top: 1rem;
  }
  
  .main {
    padding: 1rem;
  }
}
</style>
