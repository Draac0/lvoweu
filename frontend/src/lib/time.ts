// The API speaks UTC. Times are shown in the GB market's clock (UK local, GMT/BST),
// because that is how the auction and delivery days are defined. Mirrors the backend's
// MARKET_TIMEZONE setting.
const MARKET_TIMEZONE = 'Europe/London'

const timeFormat = new Intl.DateTimeFormat('en-GB', {
  timeZone: MARKET_TIMEZONE,
  hour: '2-digit',
  minute: '2-digit',
  hourCycle: 'h23',
})
const dateTimeFormat = new Intl.DateTimeFormat('en-GB', {
  timeZone: MARKET_TIMEZONE,
  day: 'numeric',
  month: 'short',
  hour: '2-digit',
  minute: '2-digit',
  hourCycle: 'h23',
})
// Day strings like "2026-01-15" are already market days; they parse as UTC midnight,
// so format them in UTC to avoid shifting the date.
const dayFormat = new Intl.DateTimeFormat('en-GB', {
  timeZone: 'UTC',
  weekday: 'short',
  day: 'numeric',
  month: 'short',
})

/** "2026-01-15T18:00:00Z" -> "18:00" */
export const marketTime = (time: string | number) => timeFormat.format(new Date(time))

/** "2026-01-14T07:30:00Z" -> "14 Jan, 07:30" */
export const marketDateTime = (time: string | number) => dateTimeFormat.format(new Date(time))

/** "2026-01-15" -> "Thu 15 Jan" */
export const formatDay = (day: string) => dayFormat.format(new Date(day))
