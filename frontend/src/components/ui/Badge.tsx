import React from 'react'
import { cn } from '@/lib/utils'

type BadgeVariant = 'default' | 'success' | 'warning' | 'error' | 'info' | 'outline'

interface BadgeProps {
  children: React.ReactNode
  variant?: BadgeVariant
  className?: string
}

const variantClasses: Record<BadgeVariant, string> = {
  default: 'bg-surface-container-low text-on-surface-variant border border-outline-variant',
  success: 'bg-emerald-50 text-emerald-700 border border-emerald-200',
  warning: 'bg-amber-50 text-amber-700 border border-amber-200',
  error: 'bg-red-50 text-error border border-red-200',
  info: 'bg-blue-50 text-blue-700 border border-blue-200',
  outline: 'bg-transparent text-on-surface-variant border border-outline-variant',
}

export const Badge: React.FC<BadgeProps> = ({ children, variant = 'default', className }) => {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-semibold tracking-wide uppercase whitespace-nowrap',
        variantClasses[variant],
        className,
      )}
    >
      {children}
    </span>
  )
}
