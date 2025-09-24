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

const getStatusClass = (week) => {
  if (week.is_current) return 'status-current'
  if (week.is_lived) return 'status-lived'
  return 'status-future'
}

const getStatusText = (week) => {
  if (week.is_current) return 'Current Week'
  if (week.is_lived) return 'Lived'
  return 'Future'
}

// Calculate year labels with proper row alignment
const getYearLabels = () => {
  if (!calendarData.value?.weeks) return []
  
  const labels = []
  const weeks = calendarData.value.weeks
  const totalYears = Math.ceil(weeks.length / 52)
  
  console.log(`Total weeks: ${weeks.length}, Total years: ${totalYears}`)
  
  // Create one label for each year of life (52 weeks each)
  for (let yearIndex = 0; yearIndex < totalYears; yearIndex++) {
    const startWeekIndex = yearIndex * 52
    const endWeekIndex = Math.min(startWeekIndex + 52, weeks.length)
    const yearWeeks = weeks.slice(startWeekIndex, endWeekIndex)
    
    if (yearWeeks.length === 0) continue
    
    // Count years in this row to find the dominant year
    const yearCounts = {}
    yearWeeks.forEach(week => {
      yearCounts[week.year] = (yearCounts[week.year] || 0) + 1
    })
    
    // Find the year with the most weeks in this row
    const dominantYear = Object.keys(yearCounts).reduce((a, b) => 
      yearCounts[a] > yearCounts[b] ? a : b
    )
    
    labels.push({
      year: parseInt(dominantYear),
      rowIndex: yearIndex
    })
  }
  
  console.log('Year labels:', labels)
  return labels
}

onMounted(() => {
  loadCalendarData()
})
</script>

<template>
  <div class="lifetime-calendar">
    <!-- Loading State -->
    <div v-if="isLoading" class="loading-container">
      <div class="loading-spinner"></div>
      <p class="loading-text">Loading your lifetime calendar...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-container">
      <div class="error-icon">⚠️</div>
      <h3 class="error-title">Unable to load calendar</h3>
      <p class="error-message">{{ error }}</p>
      <button @click="loadCalendarData" class="retry-btn">
        <span class="retry-icon">↻</span>
        Try Again
      </button>
    </div>

    <!-- Calendar Content -->
    <div v-else-if="calendarData" class="calendar-container">
      <!-- Statistics Cards -->
      <div class="stats-grid">
        <div class="stat-card glass-card lived-card">
          <div class="stat-content">
            <div class="stat-icon lived-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M9 12l2 2 4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2"/>
              </svg>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ calendarData.lived_weeks.toLocaleString() }}</div>
              <div class="stat-label">Weeks Lived</div>
            </div>
          </div>
          <div class="stat-progress">
            <div class="progress-bar" :style="{ width: `${Math.round((calendarData.lived_weeks / calendarData.total_weeks) * 100)}%` }"></div>
          </div>
        </div>
        
        <div class="stat-card glass-card remaining-card">
          <div class="stat-content">
            <div class="stat-icon remaining-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2" stroke="currentColor" stroke-width="2"/>
                <line x1="16" y1="2" x2="16" y2="6" stroke="currentColor" stroke-width="2"/>
                <line x1="8" y1="2" x2="8" y2="6" stroke="currentColor" stroke-width="2"/>
                <line x1="3" y1="10" x2="21" y2="10" stroke="currentColor" stroke-width="2"/>
              </svg>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ (calendarData.total_weeks - calendarData.lived_weeks).toLocaleString() }}</div>
              <div class="stat-label">Weeks Remaining</div>
            </div>
          </div>
          <div class="stat-progress">
            <div class="progress-bar remaining-progress" :style="{ width: `${Math.round(((calendarData.total_weeks - calendarData.lived_weeks) / calendarData.total_weeks) * 100)}%` }"></div>
          </div>
        </div>
        
        <div class="stat-card glass-card progress-card">
          <div class="stat-content">
            <div class="stat-icon progress-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M3 3v18h18" stroke="currentColor" stroke-width="2"/>
                <path d="M18.7 8l-5.1 5.2-2.8-2.7L7 14.3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ Math.round((calendarData.lived_weeks / calendarData.total_weeks) * 100) }}%</div>
              <div class="stat-label">Life Lived</div>
            </div>
          </div>
          <div class="stat-progress">
            <div class="progress-bar progress-progress" :style="{ width: `${Math.round((calendarData.lived_weeks / calendarData.total_weeks) * 100)}%` }"></div>
          </div>
        </div>
        
        <div class="stat-card glass-card years-card">
          <div class="stat-content">
            <div class="stat-icon years-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M7 10v12l5-3 5 3V10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M12 2a3 3 0 0 1 3 3v5a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3Z" stroke="currentColor" stroke-width="2"/>
              </svg>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ Math.floor(calendarData.total_weeks / 52) }}</div>
              <div class="stat-label">Total Years</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Interactive Legend -->
      <div class="legend-container">
        <h3 class="legend-title">Legend</h3>
        <div class="legend-grid">
          <div class="legend-item">
            <div class="legend-indicator lived"></div>
            <span class="legend-text">Lived</span>
          </div>
          <div class="legend-item">
            <div class="legend-indicator current"></div>
            <span class="legend-text">Current Week</span>
          </div>
          <div class="legend-item">
            <div class="legend-indicator future"></div>
            <span class="legend-text">Future</span>
          </div>
          <div class="legend-item">
            <div class="legend-indicator has-note"></div>
            <span class="legend-text">Has Note</span>
          </div>
          <div class="legend-item">
            <div class="legend-indicator year-start"></div>
            <span class="legend-text">New Year</span>
          </div>
        </div>
      </div>

      <!-- Calendar Grid -->
      <div class="calendar-section">
        <div class="calendar-grid">
          <div class="year-labels">
            <div 
              v-for="yearLabel in getYearLabels()" 
              :key="yearLabel.year" 
              class="year-label"
            >
              {{ yearLabel.year }}
            </div>
          </div>
          
          <div class="weeks-container">
            <div class="weeks-grid">
              <div 
                v-for="week in calendarData.weeks" 
                :key="week.week_number"
                :class="getWeekClass(week)"
                :title="`Week ${week.week_number} - ${formatDate(week.date)}${week.note ? '\nNote: ' + week.note : ''}`"
                @click="openWeekModal(week)"
                role="button"
                :aria-label="`Week ${week.week_number}, ${week.is_current ? 'current week' : week.is_lived ? 'lived' : 'future'}`"
                tabindex="0"
                @keydown.enter="openWeekModal(week)"
                @keydown.space.prevent="openWeekModal(week)"
              >
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Modern Week Modal -->
    <Teleport to="body">
      <div v-if="showWeekModal" class="modal-backdrop" @click="closeWeekModal">
        <div class="modal-container" @click.stop role="dialog" aria-modal="true" aria-labelledby="modal-title">
          <div class="modal-header">
            <h2 id="modal-title" class="modal-title">Week {{ selectedWeek.week_of_year }}, {{ selectedWeek.year }}</h2>
            <button 
              class="modal-close" 
              @click="closeWeekModal"
              aria-label="Close modal"
            >
              <span class="close-icon">×</span>
            </button>
          </div>
          
          <div class="modal-body">
            <div class="week-details">
              <div class="detail-item">
                <span class="detail-label">Date</span>
                <span class="detail-value">{{ formatDate(selectedWeek.date) }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Year</span>
                <span class="detail-value">{{ selectedWeek.year }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Status</span>
                <span :class="getStatusClass(selectedWeek)" class="detail-status">
                  {{ getStatusText(selectedWeek) }}
                </span>
              </div>
            </div>

            <div class="note-section">
              <label for="week-note" class="note-label">Week Note</label>
              <textarea
                id="week-note"
                v-model="weekNote"
                placeholder="Add a note about this week..."
                rows="4"
                class="note-input"
              ></textarea>
            </div>
          </div>

          <div class="modal-footer">
            <button @click="closeWeekModal" class="btn btn-secondary">
              Cancel
            </button>
            <button @click="saveWeekNote" class="btn btn-primary">
              <span class="btn-icon">💾</span>
              Save Note
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
/* Main Container */
.lifetime-calendar {
  width: 100%;
  max-width: 100%;
}

/* Loading State */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-20);
  text-align: center;
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid var(--color-border);
  border-top: 4px solid var(--color-primary-500);
  border-radius: var(--radius-full);
  animation: spin 1s linear infinite;
  margin-bottom: var(--space-4);
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-text {
  font-size: var(--font-size-lg);
  color: var(--color-text-secondary);
  margin: 0;
}

/* Error State */
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: var(--space-20);
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--color-error-200);
}

.error-icon {
  font-size: var(--font-size-4xl);
  margin-bottom: var(--space-4);
}

.error-title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-error-600);
  margin-bottom: var(--space-2);
}

.error-message {
  color: var(--color-text-secondary);
  margin-bottom: var(--space-6);
  max-width: 400px;
}

.retry-btn {
  background: var(--color-error-500);
  color: white;
  border: none;
  padding: var(--space-3) var(--space-6);
  border-radius: var(--radius-lg);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: var(--duration-fast) var(--ease-out);
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.retry-btn:hover {
  background: var(--color-error-600);
  transform: translateY(-1px);
}

.retry-icon {
  font-size: var(--font-size-lg);
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--space-6);
  margin-bottom: var(--space-8);
}

.stat-card {
  position: relative;
  overflow: hidden;
  transition: var(--duration-normal) var(--ease-out);
  transition-property: transform, box-shadow, backdrop-filter;
}

.glass-card {
  background: var(--glass-bg);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-2xl);
  box-shadow: var(--shadow-lg);
}

.stat-card:hover {
  transform: translateY(-4px) scale(1.02);
  box-shadow: var(--shadow-2xl);
}

.stat-content {
  display: flex;
  align-items: flex-start;
  gap: var(--space-4);
  padding: var(--space-6);
  position: relative;
  z-index: 2;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-xl);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: var(--duration-normal) var(--ease-out);
}

.stat-icon svg {
  width: 24px;
  height: 24px;
  stroke-width: 2.5;
}

.lived-icon {
  background: linear-gradient(135deg, var(--color-success-500), var(--color-success-600));
  color: white;
}

.remaining-icon {
  background: linear-gradient(135deg, var(--color-warning-500), var(--color-warning-600));
  color: white;
}

.progress-icon {
  background: linear-gradient(135deg, var(--color-primary-500), var(--color-primary-600));
  color: white;
}

.years-icon {
  background: linear-gradient(135deg, var(--color-neutral-600), var(--color-neutral-700));
  color: white;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-1);
  line-height: var(--line-height-tight);
  font-variant-numeric: tabular-nums;
}

.stat-label {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-progress {
  height: 4px;
  background: rgba(0, 0, 0, 0.1);
  border-radius: var(--radius-full);
  overflow: hidden;
  margin: 0 var(--space-6) var(--space-4);
}

.progress-bar {
  height: 100%;
  border-radius: var(--radius-full);
  transition: width var(--duration-slow) var(--ease-out);
  background: linear-gradient(90deg, var(--color-success-500), var(--color-success-600));
}

.remaining-progress {
  background: linear-gradient(90deg, var(--color-warning-500), var(--color-warning-600));
}

.progress-progress {
  background: linear-gradient(90deg, var(--color-primary-500), var(--color-primary-600));
}

/* Card-specific hover effects */
.lived-card:hover .lived-icon {
  transform: scale(1.1) rotate(5deg);
}

.remaining-card:hover .remaining-icon {
  transform: scale(1.1) rotate(-5deg);
}

.progress-card:hover .progress-icon {
  transform: scale(1.1) rotate(5deg);
}

.years-card:hover .years-icon {
  transform: scale(1.1) rotate(-5deg);
}

/* Legend */
.legend-container {
  background: var(--glass-bg);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  border: 1px solid var(--glass-border);
  padding: var(--space-6);
  border-radius: var(--radius-2xl);
  box-shadow: var(--shadow-lg);
  margin-bottom: var(--space-8);
  transition: var(--duration-normal) var(--ease-out);
}

.legend-container:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-xl);
}

.legend-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-4);
  text-align: center;
}

.legend-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: var(--space-4);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2);
  border-radius: var(--radius-md);
  transition: var(--duration-fast) var(--ease-out);
}

.legend-item:hover {
  background: var(--color-background-secondary);
}

.legend-indicator {
  width: 20px;
  height: 20px;
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

.legend-indicator.has-note {
  background: var(--color-surface);
  border-color: var(--color-primary-500);
  box-shadow: inset 0 0 0 2px var(--color-primary-200);
}

.legend-indicator.year-start {
  background: var(--color-surface);
  border-color: var(--color-border);
  position: relative;
}

.legend-indicator.year-start::before {
  content: '';
  position: absolute;
  left: -2px;
  top: -2px;
  bottom: -2px;
  width: 4px;
  background: var(--color-primary-500);
  border-radius: var(--radius-sm);
}

.legend-text {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-secondary);
}

/* Calendar Section */
.calendar-section {
  background: var(--glass-bg);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-2xl);
  box-shadow: var(--shadow-lg);
  overflow: hidden;
  transition: var(--duration-normal) var(--ease-out);
}

.calendar-section:hover {
  box-shadow: var(--shadow-xl);
}

.calendar-grid {
  display: flex;
  gap: var(--space-4);
  padding: var(--space-6);
  align-items: stretch;
  /* Set week box size as a custom property for consistency */
  --week-box-size: max(8px, min(1.2vw, 12px));
}

.year-labels {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex-shrink: 0;
  min-width: 60px;
  align-items: flex-end;
}

.year-label {
  display: flex;
  align-items: center;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-secondary);
  padding-right: var(--space-2);
  text-align: right;
  justify-content: flex-end;
  /* Each row contains exactly 52 weeks with gaps */
  /* Height should match one row of the weeks grid */
  flex: none;
  /* Calculate height: week box height (matches one row height) */
  height: var(--week-box-size);
  margin: 0;
}

.weeks-container {
  flex: 1;
}

.weeks-grid {
  display: grid;
  grid-template-columns: repeat(52, 1fr);
  gap: 2px;
  width: 100%;
}

.week-box {
  aspect-ratio: 1;
  width: var(--week-box-size);
  height: var(--week-box-size);
  min-width: 8px;
  min-height: 8px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  cursor: pointer;
  transition: var(--duration-fast) var(--ease-out);
  transition-property: transform, box-shadow, background-color, border-color;
  position: relative;
}

.week-box:hover {
  transform: scale(1.4);
  z-index: 10;
  box-shadow: var(--shadow-lg);
  border-width: 2px;
}

.week-box:focus {
  outline: 2px solid var(--color-primary-500);
  outline-offset: 2px;
  z-index: 10;
}

.week-box:active {
  transform: scale(1.2);
}

.week-box.lived {
  background: linear-gradient(135deg, var(--color-success-500), var(--color-success-600));
  border-color: var(--color-success-600);
  box-shadow: 0 0 3px rgba(34, 197, 94, 0.3);
}

.week-box.lived:hover {
  background: linear-gradient(135deg, var(--color-success-400), var(--color-success-500));
  box-shadow: 0 0 8px rgba(34, 197, 94, 0.5);
}

.week-box.current {
  background: linear-gradient(135deg, var(--color-warning-500), var(--color-warning-600));
  border-color: var(--color-warning-600);
  animation: pulse-gentle 2s infinite;
  box-shadow: 0 0 8px rgba(245, 158, 11, 0.4);
}

.week-box.current:hover {
  background: linear-gradient(135deg, var(--color-warning-400), var(--color-warning-500));
  box-shadow: 0 0 12px rgba(245, 158, 11, 0.6);
}

.week-box.has-note {
  box-shadow: inset 0 0 0 2px var(--color-primary-500);
}

.week-box.year-start::before {
  content: '';
  position: absolute;
  left: -3px;
  top: -1px;
  bottom: -1px;
  width: 3px;
  background: var(--color-primary-500);
  border-radius: var(--radius-sm);
}

/* Modal Styles */
.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: var(--space-4);
  animation: fadeIn var(--duration-normal) var(--ease-out);
}

@keyframes fadeIn {
  from { 
    opacity: 0; 
    backdrop-filter: blur(0px);
    -webkit-backdrop-filter: blur(0px);
  }
  to { 
    opacity: 1; 
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
  }
}

.modal-container {
  background: var(--glass-bg);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-3xl);
  box-shadow: var(--shadow-2xl);
  width: 100%;
  max-width: 520px;
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

.modal-body {
  padding: var(--space-6);
}

.week-details {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-3);
  background: var(--color-background-secondary);
  border-radius: var(--radius-lg);
}

.detail-label {
  font-weight: var(--font-weight-medium);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.detail-value {
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.detail-status {
  font-weight: var(--font-weight-semibold);
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.status-lived {
  background: var(--color-success-100);
  color: var(--color-success-700);
}

.status-current {
  background: var(--color-warning-100);
  color: var(--color-warning-700);
}

.status-future {
  background: var(--color-neutral-100);
  color: var(--color-neutral-600);
}

.note-section {
  margin-bottom: var(--space-6);
}

.note-label {
  display: block;
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-3);
  font-size: var(--font-size-sm);
}

.note-input {
  width: 100%;
  padding: var(--space-4);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  font-size: var(--font-size-base);
  font-family: var(--font-family-sans);
  resize: vertical;
  min-height: 100px;
  transition: var(--duration-fast) var(--ease-out);
  background: var(--color-surface);
  color: var(--color-text-primary);
}

.note-input:focus {
  outline: none;
  border-color: var(--color-primary-500);
  box-shadow: 0 0 0 3px var(--color-primary-100);
}

.note-input::placeholder {
  color: var(--color-text-tertiary);
}

.modal-footer {
  display: flex;
  gap: var(--space-3);
  justify-content: flex-end;
  padding: var(--space-6);
  border-top: 1px solid var(--color-border);
  background: var(--color-background-secondary);
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
}

.btn-secondary {
  background: var(--color-background-tertiary);
  color: var(--color-text-secondary);
}

.btn-secondary:hover {
  background: var(--color-border);
  color: var(--color-text-primary);
}

.btn-primary {
  background: var(--color-primary-500);
  color: white;
}

.btn-primary:hover {
  background: var(--color-primary-600);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.btn-icon {
  font-size: var(--font-size-base);
}

/* Responsive Design */
@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: var(--space-4);
  }
  
  .legend-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: var(--space-3);
  }
  
  .calendar-grid {
    padding: var(--space-4);
    gap: var(--space-2);
    --week-box-size: max(6px, min(1vw, 10px));
  }
  
  .year-labels {
    min-width: 50px;
  }
  
  .year-label {
    font-size: 10px;
  }
  
  .weeks-grid {
    grid-template-columns: repeat(52, 1fr);
    gap: 1px;
  }
  
  .week-box {
    min-width: 6px;
    min-height: 6px;
  }
  
  .modal-container {
    margin: var(--space-4);
  }
  
  .modal-header,
  .modal-body,
  .modal-footer {
    padding: var(--space-4);
  }
  
  .modal-footer {
    flex-direction: column;
  }
  
  .btn {
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .legend-grid {
    grid-template-columns: 1fr;
  }
  
  .calendar-grid {
    --week-box-size: max(4px, min(0.8vw, 6px));
  }
  
  .weeks-grid {
    grid-template-columns: repeat(52, 1fr);
    gap: 1px;
  }
  
  .week-box {
    min-width: 4px;
    min-height: 4px;
  }
  
  .year-label {
    font-size: 9px;
  }
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  .week-box,
  .stat-card,
  .modal-container,
  .modal-backdrop {
    animation: none;
  }
  
  .week-box.current {
    animation: none;
  }
  
  .legend-indicator.current {
    animation: none;
  }
}

/* High contrast mode */
@media (prefers-contrast: high) {
  .week-box {
    border-width: 2px;
  }
  
  .legend-indicator {
    border-width: 3px;
  }
}
</style>