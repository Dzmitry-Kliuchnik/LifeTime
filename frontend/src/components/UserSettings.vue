<script setup>
import { ref, defineProps, defineEmits, onMounted } from 'vue'
import axios from 'axios'

const props = defineProps({
  userData: Object
})

const emit = defineEmits(['user-saved', 'close'])

const API_BASE = 'http://localhost:8000'

const birthdate = ref('')
const lifeExpectancy = ref(80)
const isLoading = ref(false)
const error = ref('')

const saveUserData = async () => {
  if (!birthdate.value) {
    error.value = 'Please enter your birthdate'
    return
  }

  isLoading.value = true
  error.value = ''

  try {
    await axios.post(`${API_BASE}/api/user`, {
      birthdate: birthdate.value,
      life_expectancy: lifeExpectancy.value
    })

    emit('user-saved', {
      birthdate: birthdate.value,
      life_expectancy: lifeExpectancy.value
    })
  } catch (err) {
    error.value = 'Failed to save user data. Please try again.'
    console.error('Error saving user data:', err)
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  if (props.userData) {
    birthdate.value = props.userData.birthdate
    lifeExpectancy.value = props.userData.life_expectancy
  }
})
</script>

<template>
  <div class="settings-overlay">
    <div class="settings-modal">
      <div class="modal-header">
        <h2>⚙️ Settings</h2>
        <button class="close-btn" @click="emit('close')">×</button>
      </div>

      <form @submit.prevent="saveUserData" class="settings-form">
        <div class="form-group">
          <label for="birthdate">Your Birthdate:</label>
          <input
            id="birthdate"
            type="date"
            v-model="birthdate"
            required
            class="form-input"
          />
          <small class="form-help">This is used to calculate which weeks you've already lived</small>
        </div>

        <div class="form-group">
          <label for="life-expectancy">Life Expectancy (years):</label>
          <input
            id="life-expectancy"
            type="number"
            v-model="lifeExpectancy"
            min="1"
            max="120"
            required
            class="form-input"
          />
          <small class="form-help">Average life expectancy varies by country (typically 70-85 years)</small>
        </div>

        <div class="info-box">
          <h3>About Lifetime Calendar</h3>
          <p>This calendar shows every week of your life as a box. Each row represents one year (52 weeks), and you can see:</p>
          <ul>
            <li><span class="lived-box"></span> Weeks you've already lived (filled)</li>
            <li><span class="current-box"></span> Your current week (highlighted)</li>
            <li><span class="future-box"></span> Future weeks (empty)</li>
          </ul>
          <p>It's inspired by the "Your Life in Weeks" concept to help visualize time and make the most of it.</p>
        </div>

        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <div class="form-actions">
          <button type="button" @click="emit('close')" class="btn btn-secondary">
            Cancel
          </button>
          <button type="submit" :disabled="isLoading" class="btn btn-primary">
            {{ isLoading ? 'Saving...' : 'Save & Continue' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.settings-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.settings-modal {
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #eee;
}

.modal-header h2 {
  font-size: 1.5rem;
  color: #333;
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  font-size: 2rem;
  color: #999;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background: #f5f5f5;
  color: #666;
}

.settings-form {
  padding: 1.5rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  font-weight: 600;
  color: #333;
  margin-bottom: 0.5rem;
}

.form-input {
  width: 100%;
  padding: 0.75rem;
  border: 2px solid #ddd;
  border-radius: 6px;
  font-size: 1rem;
  transition: border-color 0.2s ease;
}

.form-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-help {
  display: block;
  color: #666;
  font-size: 0.875rem;
  margin-top: 0.25rem;
}

.info-box {
  background: #f8f9ff;
  border: 1px solid #e1e5ff;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1.5rem;
}

.info-box h3 {
  color: #333;
  font-size: 1rem;
  margin-bottom: 0.5rem;
}

.info-box p {
  color: #666;
  font-size: 0.875rem;
  line-height: 1.5;
  margin-bottom: 0.5rem;
}

.info-box ul {
  margin: 0.5rem 0;
  padding-left: 1rem;
}

.info-box li {
  color: #666;
  font-size: 0.875rem;
  line-height: 1.5;
  display: flex;
  align-items: center;
  margin-bottom: 0.25rem;
}

.lived-box, .current-box, .future-box {
  width: 12px;
  height: 12px;
  border: 1px solid #ddd;
  margin-right: 0.5rem;
  border-radius: 2px;
}

.lived-box {
  background: #4ade80;
}

.current-box {
  background: #f59e0b;
  border-color: #f59e0b;
}

.future-box {
  background: white;
}

.error-message {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
  padding: 0.75rem;
  border-radius: 6px;
  margin-bottom: 1rem;
  font-size: 0.875rem;
}

.form-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 2rem;
}

.btn {
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
}

.btn-secondary {
  background: #f3f4f6;
  color: #374151;
}

.btn-secondary:hover {
  background: #e5e7eb;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3);
}

.btn-primary:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

@media (max-width: 480px) {
  .form-actions {
    flex-direction: column;
  }
  
  .btn {
    width: 100%;
  }
}
</style>