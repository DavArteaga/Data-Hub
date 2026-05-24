import { clsx, type ClassValue } from 'clsx'

/** Merge class names safely */
export function cn(...inputs: ClassValue[]) {
  return clsx(inputs)
}

/** Format a numeric value as Colombian currency (COP millions) or plain number */
export function formatValue(value: number | string, unit?: string): string {
  const num = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(num)) return String(value)

  if (unit === 'COP' || unit === 'COP_M') {
    if (Math.abs(num) >= 1_000_000) {
      return `${(num / 1_000_000).toLocaleString('es-CO', { maximumFractionDigits: 1 })} M COP`
    }
    if (Math.abs(num) >= 1_000) {
      return `${(num / 1_000).toLocaleString('es-CO', { maximumFractionDigits: 1 })} K COP`
    }
    return `${num.toLocaleString('es-CO')} COP`
  }

  if (unit === 'empleados' || unit === 'personas') {
    return num.toLocaleString('es-CO')
  }

  return num.toLocaleString('es-CO', { maximumFractionDigits: 2 })
}

/** Format score as percentage string */
export function formatScore(score: number): string {
  return `${(score * 100).toFixed(1)}%`
}

/** Get color class based on score thresholds */
export function scoreColor(score: number): { text: string; bg: string; hex: string } {
  if (score > 0.85) return { text: 'text-emerald-700', bg: 'bg-emerald-100', hex: '#059669' }
  if (score >= 0.65) return { text: 'text-amber-700', bg: 'bg-amber-100', hex: '#d97706' }
  return { text: 'text-red-700', bg: 'bg-red-100', hex: '#dc2626' }
}

/** Relative time from ISO string */
export function relativeTime(isoString: string): string {
  const date = new Date(isoString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMin = Math.floor(diffMs / 60_000)
  const diffHr = Math.floor(diffMin / 60)
  const diffDay = Math.floor(diffHr / 24)

  if (diffMin < 1) return 'Hace un momento'
  if (diffMin < 60) return `Hace ${diffMin} min`
  if (diffHr < 24) return `Hace ${diffHr} h`
  if (diffDay < 7) return `Hace ${diffDay} días`
  return date.toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })
}

/** Truncate text with ellipsis */
export function truncate(str: string, n: number): string {
  return str.length > n ? str.slice(0, n - 1) + '…' : str
}
