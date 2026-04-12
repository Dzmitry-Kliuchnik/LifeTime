export function computeEndDate(birthdate, lifeExpectancy) {
  const [year, month, day] = birthdate.split('-').map(Number)
  const endDate = new Date(Date.UTC(year + lifeExpectancy, month - 1, day))
  return endDate
}

export function formatCountdown(totalSeconds) {
  const s = Math.floor(Math.max(0, totalSeconds))
  const d = Math.floor(s / 86400)
  const h = Math.floor((s % 86400) / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = s % 60
  return `${d.toLocaleString()}d ${h}h ${String(m).padStart(2, '0')}m ${String(sec).padStart(2, '0')}s`
}
