import React from 'react'
import { cn } from '@/lib/utils'

type Variant = 'primary' | 'ghost' | 'outline' | 'danger'
type Size = 'sm' | 'md' | 'lg'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
  loading?: boolean
  children: React.ReactNode
}

const variantClasses: Record<Variant, string> = {
  primary:
    'bg-primary-container text-white hover:bg-[#1a347e] active:bg-[#162d6e] shadow-sm',
  ghost:
    'bg-transparent text-on-surface-variant hover:bg-surface-container-low active:bg-outline-variant/30',
  outline:
    'bg-transparent border border-outline-variant text-on-surface hover:bg-surface-container-low',
  danger:
    'bg-error text-white hover:bg-red-700 active:bg-red-800',
}

const sizeClasses: Record<Size, string> = {
  sm: 'h-7 px-3 text-[12px] gap-1.5',
  md: 'h-9 px-4 text-[14px] gap-2',
  lg: 'h-11 px-5 text-[15px] gap-2',
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', size = 'md', loading = false, className, children, disabled, ...props }, ref) => {
    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={cn(
          'inline-flex items-center justify-center font-medium rounded-btn transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-container/50 disabled:opacity-50 disabled:cursor-not-allowed select-none',
          variantClasses[variant],
          sizeClasses[size],
          className,
        )}
        {...props}
      >
        {loading ? (
          <svg className="animate-spin h-4 w-4 shrink-0" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
        ) : null}
        {children}
      </button>
    )
  },
)

Button.displayName = 'Button'
