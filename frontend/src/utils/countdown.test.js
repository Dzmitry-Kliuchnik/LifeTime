import { describe, it, expect } from 'vitest'
import { computeEndDate, formatCountdown } from './countdown.js'

describe('computeEndDate', () => {
  it('returns a Date that is birthdate + life_expectancy years', () => {
    const result = computeEndDate('1990-01-01', 80)
    expect(result).toBeInstanceOf(Date)
    expect(result.getFullYear()).toBe(2070)
    expect(result.getMonth()).toBe(0) // January
    expect(result.getDate()).toBe(1)
  })

  it('handles leap year birthdays', () => {
    const result = computeEndDate('2000-02-29', 30)
    expect(result).toBeInstanceOf(Date)
    // 2030 is not a leap year, so Feb 29 overflows to Mar 1
    expect(result.getUTCFullYear()).toBe(2030)
    expect(result.getUTCMonth()).toBe(2) // March (0-indexed)
    expect(result.getUTCDate()).toBe(1)
    // UTC-consistent: time component is zero (no timezone shift)
    expect(result.getUTCHours()).toBe(0)
    expect(result.getUTCMinutes()).toBe(0)
    expect(result.getUTCSeconds()).toBe(0)
  })
})

describe('formatCountdown', () => {
  it('formats zero seconds', () => {
    expect(formatCountdown(0)).toBe('0d 0h 00m 00s')
  })

  it('formats exactly one day', () => {
    expect(formatCountdown(86400)).toBe('1d 0h 00m 00s')
  })

  it('formats hours minutes seconds', () => {
    expect(formatCountdown(3661)).toBe('0d 1h 01m 01s')
  })

  it('formats large values with locale separators for days', () => {
    // 21380 days
    const seconds = 21380 * 86400
    const result = formatCountdown(seconds)
    expect(result).toMatch(/21[,.]?380d/)
  })

  it('pads minutes and seconds to 2 digits', () => {
    expect(formatCountdown(61)).toBe('0d 0h 01m 01s')
  })

  it('clamps negative seconds to zero', () => {
    expect(formatCountdown(-100)).toBe('0d 0h 00m 00s')
  })
})
