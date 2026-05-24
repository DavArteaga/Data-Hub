import React from 'react'
import { scoreColor } from '@/lib/utils'

interface ScoreCircleProps {
  score: number
  size?: number
  label?: string
  showLabel?: boolean
}

export const ScoreCircle: React.FC<ScoreCircleProps> = ({
  score,
  size = 96,
  label,
  showLabel = true,
}) => {
  const radius = (size - 12) / 2
  const circumference = 2 * Math.PI * radius
  const progress = Math.max(0, Math.min(1, score))
  const dashOffset = circumference * (1 - progress)
  const { hex } = scoreColor(score)
  const pct = Math.round(score * 100)

  const center = size / 2
  const strokeWidth = size > 80 ? 8 : 6

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          {/* Background track */}
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke="#e5e7eb"
            strokeWidth={strokeWidth}
          />
          {/* Progress arc */}
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke={hex}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={dashOffset}
            transform={`rotate(-90 ${center} ${center})`}
            style={{ transition: 'stroke-dashoffset 0.6s ease' }}
          />
        </svg>
        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span
            className="font-bold leading-none"
            style={{ fontSize: size > 80 ? size * 0.22 : size * 0.24, color: hex }}
          >
            {pct}
          </span>
          <span
            className="text-on-surface-variant leading-none mt-0.5"
            style={{ fontSize: size > 80 ? size * 0.1 : size * 0.12 }}
          >
            /100
          </span>
        </div>
      </div>
      {showLabel && label && (
        <span className="text-[12px] text-on-surface-variant text-center max-w-[140px] leading-snug">
          {label}
        </span>
      )}
    </div>
  )
}
