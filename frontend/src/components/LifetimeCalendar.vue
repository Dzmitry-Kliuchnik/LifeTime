<script setup>
import { ref, onMounted, defineProps } from 'vue'
import axios from 'axios'

const props = defineProps({
  userData: Object
})

const API_BASE = 'http://localhost:8000'

const calendarData = ref(null)
const isLoading = ref(true)
const error = ref('')
const selectedWeek = ref(null)
const showWeekModal = ref(false)
const weekNote = ref('')

const loadCalendarData = async () => {
  isLoading.value = true
  error.value = ''

  try {
    const response = await axios.get(`${API_BASE}/api/calendar`)
    calendarData.value = response.data
  } catch (err) {
    error.value = 'Failed to load calendar data. Please check your settings.'
    console.error('Error loading calendar data:', err)
  } finally {
    isLoading.value = false
  }
}

const openWeekModal = (week) => {
  selectedWeek.value = week
  weekNote.value = week.note || ''
  showWeekModal.value = true
}

const closeWeekModal = () => {
  showWeekModal.value = false
  selectedWeek.value = null
  weekNote.value = ''
}

const saveWeekNote = async () => {
  if (!selectedWeek.value) return

  try {
    await axios.post(`${API_BASE}/api/week-note`, {
      week_number: selectedWeek.value.week_of_year,
      year: selectedWeek.value.year,
      note: weekNote.value,
      is_lived: selectedWeek.value.is_lived
    })

    // Update the week in calendar data
    const weekIndex = calendarData.value.weeks.findIndex(w => 
      w.week_number === selectedWeek.value.week_number
    )
    if (weekIndex !== -1) {
      calendarData.value.weeks[weekIndex].note = weekNote.value
    }

    closeWeekModal()
  } catch (err) {
    console.error('Error saving week note:', err)
    alert('Failed to save note. Please try again.')
  }
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { 
    year: 'numeric', 
    month: 'short', 
    day: 'numeric' 
  })
}

const getWeekClass = (week) => {
  let classes = ['week-box']
  
  if (week.is_lived) {
    classes.push('lived')
  }
  
  if (week.is_current) {
    classes.push('current')
  }
  
  if (week.note) {
    classes.push('has-note')
  }

  // Mark the first week of each calendar year
  if (week.week_of_year === 1) {
    classes.push('year-start')
  }
  
  return classes.join(' ')
}

onMounted(() => {
  loadCalendarData()
})
</script>

<template>
  <div class="lifetime-calendar">
    <div v-if="isLoading" class="loading">
      Loading your lifetime calendar...
    </div>

    <div v-else-if="error" class="error">
      {{ error }}
    </div>

    <div v-else-if="calendarData" class="calendar-container">
      <!-- Statistics -->
      <div class="stats">
        <div class="stat-item">
          <div class="stat-number">{{ calendarData.lived_weeks }}</div>
          <div class="stat-label">Weeks Lived</div>
        </div>
        <div class="stat-item">
          <div class="stat-number">{{ calendarData.total_weeks - calendarData.lived_weeks }}</div>
          <div class="stat-label">Weeks Remaining</div>
        </div>
        <div class="stat-item">
          <div class="stat-number">{{ Math.round((calendarData.lived_weeks / calendarData.total_weeks) * 100) }}%</div>
          <div class="stat-label">Life Lived</div>
        </div>
        <div class="stat-item">
          <div class="stat-number">{{ Math.floor(calendarData.total_weeks / 52) }}</div>
          <div class="stat-label">Total Years</div>
        </div>
      </div>

      <!-- Legend -->
      <div class="legend">
        <div class="legend-item">
          <div class="legend-box lived"></div>
          <span>Lived</span>
        </div>
        <div class="legend-item">
          <div class="legend-box current"></div>
          <span>Current Week</span>
        </div>
        <div class="legend-item">
          <div class="legend-box future"></div>
          <span>Future</span>
        </div>
        <div class="legend-item">
          <div class="legend-box has-note"></div>
          <span>Has Note</span>
        </div>
        <div class="legend-item">
          <div class="legend-box year-start"></div>
          <span>New Year</span>
        </div>
      </div>

      <!-- Calendar Grid -->
      <div class="calendar-grid">
        <div class="year-labels">
          <div 
            v-for="year in Math.ceil(calendarData.total_weeks / 52)" 
            :key="year" 
            class="year-label"
          >
            {{ new Date(props.userData.birthdate).getFullYear() + year - 1 }}
          </div>
        </div>
        
        <div class="weeks-grid">
          <div 
            v-for="week in calendarData.weeks" 
            :key="week.week_number"
            :class="getWeekClass(week)"
            :title="`Week ${week.week_number} - ${formatDate(week.date)}`"
            @click="openWeekModal(week)"
          >
          </div>
        </div>
      </div>
    </div>

    <!-- Week Modal -->
    <div v-if="showWeekModal" class="modal-overlay" @click="closeWeekModal">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h3>Week {{ selectedWeek.week_number }}</h3>
          <button class="close-btn" @click="closeWeekModal">×</button>
        </div>
        
        <div class="modal-content">
          <div class="week-info">
            <p><strong>Date:</strong> {{ formatDate(selectedWeek.date) }}</p>
            <p><strong>Year:</strong> {{ selectedWeek.year }}</p>
            <p><strong>Status:</strong> 
              <span :class="{ 
                'status-lived': selectedWeek.is_lived,
                'status-current': selectedWeek.is_current,
                'status-future': !selectedWeek.is_lived && !selectedWeek.is_current
              }">
                {{ selectedWeek.is_current ? 'Current Week' : selectedWeek.is_lived ? 'Lived' : 'Future' }}
              </span>
            </p>
          </div>

          <div class="note-section">
            <label for="week-note">Week Note:</label>
            <textarea
              id="week-note"
              v-model="weekNote"
              placeholder="Add a note about this week..."
              rows="4"
              class="note-textarea"
            ></textarea>
          </div>

          <div class="modal-actions">
            <button @click="closeWeekModal" class="btn btn-secondary">Cancel</button>
            <button @click="saveWeekNote" class="btn btn-primary">Save Note</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.lifetime-calendar {
  max-width: 100%;
  margin: 0 auto;
}

.loading, .error {
  text-align: center;
  padding: 4rem 2rem;
  font-size: 1.2rem;
}

.error {
  color: #dc2626;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
}

.stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-item {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.stat-number {
  font-size: 2rem;
  font-weight: 700;
  color: #667eea;
  margin-bottom: 0.5rem;
}

.stat-label {
  color: #666;
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 2rem;
  justify-content: center;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: #666;
}

.legend-box {
  width: 16px;
  height: 16px;
  border: 1px solid #ddd;
  border-radius: 2px;
}

.legend-box.lived {
  background: #4ade80;
  border-color: #22c55e;
}

.legend-box.current {
  background: #f59e0b;
  border-color: #d97706;
  animation: pulse 2s infinite;
}

.legend-box.future {
  background: white;
  border-color: #e5e7eb;
}

.legend-box.has-note {
  background: white;
  border-color: #e5e7eb;
  box-shadow: inset 0 0 0 2px #8b5cf6;
}

/* Legend sample for year start */
.legend-box.year-start {
  background: white;
  border-color: #e5e7eb;
  box-shadow: inset 3px 0 0 #3b82f6; /* blue tick on the left */
}

.calendar-grid {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  gap: 1rem;
}

.year-labels {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.year-label {
  height: 12px;
  display: flex;
  align-items: center;
  font-size: 0.75rem;
  color: #666;
  padding-right: 0.5rem;
  line-height: 1;
}

.weeks-grid {
  display: grid;
  grid-template-columns: repeat(52, 12px);
  gap: 2px;
  flex: 1;
}

.week-box {
  width: 12px;
  height: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 2px;
  cursor: pointer;
  transition: all 0.2s ease;
  background: white;
  position: relative; /* for year-start marker */
}

/* Visual marker for the first week of each year */
.week-box.year-start {
  box-shadow: inset 3px 0 0 #3b82f6; /* blue left tick */
}

.week-box:hover {
  transform: scale(1.2);
  border-color: #667eea;
  z-index: 10;
  position: relative;
}

.week-box.lived {
  background: #4ade80;
  border-color: #22c55e;
}

.week-box.current {
  background: #f59e0b;
  border-color: #d97706;
  animation: pulse 2s infinite;
}

.week-box.has-note {
  box-shadow: inset 0 0 0 2px #8b5cf6;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

/* Modal Styles */
.modal-overlay {
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

.modal {
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 500px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
  color: #333;
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

.modal-content {
  padding: 1.5rem;
}

.week-info {
  margin-bottom: 1.5rem;
}

.week-info p {
  margin-bottom: 0.5rem;
  color: #333;
}

.status-lived {
  color: #22c55e;
  font-weight: 600;
}

.status-current {
  color: #f59e0b;
  font-weight: 600;
}

.status-future {
  color: #6b7280;
  font-weight: 600;
}

.note-section {
  margin-bottom: 1.5rem;
}

.note-section label {
  display: block;
  font-weight: 600;
  color: #333;
  margin-bottom: 0.5rem;
}

.note-textarea {
  width: 100%;
  padding: 0.75rem;
  border: 2px solid #ddd;
  border-radius: 6px;
  font-size: 1rem;
  font-family: inherit;
  resize: vertical;
  transition: border-color 0.2s ease;
}

.note-textarea:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.modal-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
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

.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3);
}

/* Responsive Design */
@media (max-width: 768px) {
  .calendar-grid {
    padding: 1rem;
    flex-direction: column;
  }
  
  .year-labels {
    flex-direction: row;
    overflow-x: auto;
    gap: 0.5rem;
    margin-bottom: 1rem;
  }
  
  .year-label {
    height: auto;
    white-space: nowrap;
    padding: 0.25rem 0.5rem;
    background: #f3f4f6;
    border-radius: 4px;
  }
  
  .weeks-grid {
    grid-template-columns: repeat(26, 1fr);
    max-width: 100%;
  }
  
  .week-box {
    width: 100%;
    height: 12px;
  }
  
  .modal-actions {
    flex-direction: column;
  }
}

@media (max-width: 480px) {
  .weeks-grid {
    grid-template-columns: repeat(13, 1fr);
  }
  
  .stats {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
