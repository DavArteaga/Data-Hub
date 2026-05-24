import React from 'react'
import { cn, scoreColor } from '@/lib/utils'

interface ScoreBarProps {
  score: number
  label?: string
  showValue?: boolean
  height?: number
  className?: string
}

export const ScoreBar: React.FC<ScoreBarProps> = ({
  score,
  label,
  showValue = true,
  height = 6,
  className,
}) => {
  const pct = Math.round(Math.max(0, Math.min(1, score)) * 100)
  const { hex, text } = scoreColor(score)

  return (
    <div className={cn('w-full', className)}>
      {(label || showValue) && (
        <div className="flex justify-between items-center mb-1">
          {label && <span className="text-[12px] text-on-surface-variant">{label}</span>}
          {showValue && (
            <span className={cn('text-[12px] font-semibold tabular-nums', text)}>
              {pct}%
            </span>
          )}
        </div>
      )}
      <div
        className="w-full rounded-full overflow-hidden bg-gray-100"
        style={{ height }}
      >
        <div
          className="h-full rounded-full transition-all duration-500 ease-out"
          style={{ width: `${pct}%`, backgroundColor: hex }}
        />
      </div>
    </div>
  )
}
