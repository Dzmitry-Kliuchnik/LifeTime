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

  const birthdateObj = new Date(birthdate.value)
  const today = new Date()
  
  if (birthdateObj > today) {
    error.value = 'Birthdate cannot be in the future'
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

const closeModal = () => {
  emit('close')
}

onMounted(() => {
  if (props.userData) {
    birthdate.value = props.userData.birthdate
    lifeExpectancy.value = props.userData.life_expectancy
  }
})
</script>

<template>
  <Teleport to="body">
    <div class="modal-backdrop" @click="closeModal">
      <div class="modal-container" @click.stop role="dialog" aria-modal="true" aria-labelledby="settings-title">
        <div class="modal-header">
          <h2 id="settings-title" class="modal-title">
            <span class="settings-icon">⚙️</span>
            Settings
          </h2>
          <button 
            class="modal-close" 
            @click="closeModal"
            aria-label="Close settings"
          >
            <span class="close-icon">×</span>
          </button>
        </div>

        <form @submit.prevent="saveUserData" class="modal-body">
          <div v-if="error" class="error-message" role="alert">
            <span class="error-icon">⚠️</span>
            {{ error }}
          </div>

          <div class="form-section">
            <div class="form-group">
              <label for="birthdate" class="form-label">Your Birthdate:</label>
              <input
                id="birthdate"
                type="date"
                v-model="birthdate"
                required
                class="form-input"
                :disabled="isLoading"
              />
              <p class="form-help">This is used to calculate which weeks you've already lived</p>
            </div>

            <div class="form-group">
              <label for="life-expectancy" class="form-label">Life Expectancy (years):</label>
              <input
                id="life-expectancy"
                type="number"
                v-model="lifeExpectancy"
                min="1"
                max="120"
                required
                class="form-input"
                :disabled="isLoading"
              />
              <p class="form-help">Average life expectancy varies by country (typically 70-85 years)</p>
            </div>
          </div>

          <div class="info-section">
            <h3 class="info-title">About Lifetime Calendar</h3>
            <p class="info-text">This calendar shows every week of your life as a box. Each row represents one year (52 weeks), and you can see:</p>
            <ul class="legend-list">
              <li class="legend-item">
                <div class="legend-indicator lived"></div>
                <span>Weeks you've already lived (filled)</span>
              </li>
              <li class="legend-item">
                <div class="legend-indicator current"></div>
                <span>Your current week (highlighted)</span>
              </li>
              <li class="legend-item">
                <div class="legend-indicator future"></div>
                <span>Future weeks (empty)</span>
              </li>
            </ul>
            <p class="info-text">It's inspired by the "Your Life in Weeks" concept to help visualize time and make the most of it.</p>
          </div>

          <div class="form-actions">
            <button type="button" @click="closeModal" class="btn btn-secondary" :disabled="isLoading">
              Cancel
            </button>
            <button type="submit" :disabled="isLoading" class="btn btn-primary">
              <span v-if="isLoading" class="btn-spinner"></span>
              <span class="btn-icon" v-if="!isLoading">💾</span>
              {{ isLoading ? 'Saving...' : 'Save & Continue' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
/* Modal Backdrop */
.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: var(--space-4);
  animation: fadeIn var(--duration-normal) var(--ease-out);
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Modal Container */
.modal-container {
  background: var(--color-surface);
  border-radius: var(--radius-2xl);
  box-shadow: var(--shadow-2xl);
  width: 100%;
  max-width: 600px;
  max-height: 90vh;
  overflow: hidden;
  animation: slideIn var(--duration-normal) var(--ease-out);
}

@keyframes slideIn {
  from { 
    opacity: 0; 
    transform: translateY(-20px) scale(0.95); 
  }
  to { 
    opacity: 1; 
    transform: translateY(0) scale(1); 
  }
}

/* Modal Header */
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-6);
  border-bottom: 1px solid var(--color-border);
  background: var(--color-background-secondary);
}

.modal-title {
  margin: 0;
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.settings-icon {
  font-size: var(--font-size-lg);
}

.modal-close {
  background: none;
  border: none;
  color: var(--color-text-secondary);
  cursor: pointer;
  padding: var(--space-2);
  border-radius: var(--radius-full);
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: var(--duration-fast) var(--ease-out);
}

.modal-close:hover {
  background: var(--color-background-tertiary);
  color: var(--color-text-primary);
}

.close-icon {
  font-size: var(--font-size-xl);
  line-height: 1;
}

/* Modal Body */
.modal-body {
  padding: var(--space-6);
  overflow-y: auto;
}

/* Error Message */
.error-message {
  background: var(--color-error-50);
  border: 1px solid var(--color-error-200);
  color: var(--color-error-700);
  padding: var(--space-4);
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-6);
  font-size: var(--font-size-sm);
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.error-icon {
  font-size: var(--font-size-base);
  flex-shrink: 0;
}

/* Form Section */
.form-section {
  margin-bottom: var(--space-8);
}

.form-group {
  margin-bottom: var(--space-6);
}

.form-label {
  display: block;
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-2);
  font-size: var(--font-size-sm);
}

.form-input {
  width: 100%;
  padding: var(--space-4);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  font-size: var(--font-size-base);
  font-family: var(--font-family-sans);
  transition: var(--duration-fast) var(--ease-out);
  background: var(--color-surface);
  color: var(--color-text-primary);
}

.form-input:focus {
  outline: none;
  border-color: var(--color-primary-500);
  box-shadow: 0 0 0 3px var(--color-primary-100);
}

.form-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background: var(--color-background-secondary);
}

.form-help {
  margin-top: var(--space-2);
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
  line-height: var(--line-height-normal);
}

/* Info Section */
.info-section {
  background: var(--color-primary-50);
  border: 1px solid var(--color-primary-200);
  border-radius: var(--radius-xl);
  padding: var(--space-6);
  margin-bottom: var(--space-8);
}

.info-title {
  color: var(--color-text-primary);
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  margin-bottom: var(--space-4);
}

.info-text {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  line-height: var(--line-height-normal);
  margin-bottom: var(--space-4);
}

.legend-list {
  margin: var(--space-4) 0;
  padding: 0;
  list-style: none;
}

.legend-item {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  line-height: var(--line-height-normal);
  display: flex;
  align-items: center;
  margin-bottom: var(--space-3);
  gap: var(--space-3);
}

.legend-indicator {
  width: 16px;
  height: 16px;
  border-radius: var(--radius-sm);
  border: 2px solid var(--color-border);
  flex-shrink: 0;
}

.legend-indicator.lived {
  background: var(--color-success-500);
  border-color: var(--color-success-600);
}

.legend-indicator.current {
  background: var(--color-warning-500);
  border-color: var(--color-warning-600);
  animation: pulse-gentle 2s infinite;
}

@keyframes pulse-gentle {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.legend-indicator.future {
  background: var(--color-surface);
  border-color: var(--color-border);
}

/* Form Actions */
.form-actions {
  display: flex;
  gap: var(--space-3);
  justify-content: flex-end;
  padding-top: var(--space-6);
  border-top: 1px solid var(--color-border);
}

.btn {
  padding: var(--space-3) var(--space-6);
  border-radius: var(--radius-lg);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
  transition: var(--duration-fast) var(--ease-out);
  border: none;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  min-width: 120px;
  justify-content: center;
}

.btn-secondary {
  background: var(--color-background-tertiary);
  color: var(--color-text-secondary);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--color-border);
  color: var(--color-text-primary);
}

.btn-primary {
  background: var(--color-primary-500);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: var(--color-primary-600);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
}

.btn-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid transparent;
  border-top: 2px solid currentColor;
  border-radius: var(--radius-full);
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.btn-icon {
  font-size: var(--font-size-base);
}

/* Responsive Design */
@media (max-width: 768px) {
  .modal-container {
    margin: var(--space-4);
    max-height: calc(100vh - 2rem);
  }
  
  .modal-header,
  .modal-body {
    padding: var(--space-4);
  }
  
  .form-actions {
    flex-direction: column;
    gap: var(--space-2);
  }
  
  .btn {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .modal-title {
    font-size: var(--font-size-lg);
  }
  
  .form-section {
    margin-bottom: var(--space-6);
  }
  
  .info-section {
    padding: var(--space-4);
    margin-bottom: var(--space-6);
  }
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  .modal-backdrop,
  .modal-container,
  .legend-indicator.current,
  .btn-spinner {
    animation: none;
  }
}

/* High contrast mode */
@media (prefers-contrast: high) {
  .form-input {
    border-width: 3px;
  }
  
  .legend-indicator {
    border-width: 3px;
  }
}
</style>