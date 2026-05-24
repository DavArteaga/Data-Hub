import React from 'react'
import { cn } from '@/lib/utils'

interface CardProps {
  children: React.ReactNode
  className?: string
  padding?: boolean
}

export const Card: React.FC<CardProps> = ({ children, className, padding = true }) => {
  return (
    <div
      className={cn(
        'bg-surface rounded-card border border-outline-variant',
        padding && 'p-5',
        className,
      )}
    >
      {children}
    </div>
  )
}

interface CardHeaderProps {
  title: string
  subtitle?: string
  action?: React.ReactNode
  className?: string
}

export const CardHeader: React.FC<CardHeaderProps> = ({ title, subtitle, action, className }) => {
  return (
    <div className={cn('flex items-start justify-between mb-4', className)}>
      <div>
        <h3 className="text-[14px] font-semibold text-on-surface">{title}</h3>
        {subtitle && <p className="text-[12px] text-on-surface-variant mt-0.5">{subtitle}</p>}
      </div>
      {action && <div className="shrink-0 ml-3">{action}</div>}
    </div>
  )
}
