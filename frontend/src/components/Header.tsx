import React from 'react'
import { useLocation, Link } from 'react-router-dom'
import { Bell, Settings, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/Button'

interface Crumb {
  label: string
  to?: string
}

function useBreadcrumbs(): Crumb[] {
  const { pathname } = useLocation()
  const segments = pathname.split('/').filter(Boolean)

  if (segments.length === 0) return [{ label: 'Inicio' }]

  const crumbs: Crumb[] = [{ label: 'Inicio', to: '/' }]

  if (segments[0] === 'api-explorer') {
    crumbs.push({ label: 'API Explorer' })
  } else if (segments[0] === 'bitacora') {
    crumbs.push({ label: 'Bitácora' })
  } else if (segments[0] === 'empresas') {
    crumbs.push({ label: 'Empresas', to: '/' })
    if (segments[1]) {
      crumbs.push({ label: segments[1], to: `/empresas/${segments[1]}` })
    }
    if (segments[2] === 'score' && segments[3]) {
      crumbs.push({ label: 'Score', to: `/empresas/${segments[1]}/score/${segments[3]}` })
      crumbs.push({ label: segments[3].toUpperCase() })
    }
  }

  return crumbs
}

export const Header: React.FC = () => {
  const crumbs = useBreadcrumbs()

  return (
    <header
      className="fixed top-0 right-0 z-20 flex items-center justify-between bg-surface border-b border-outline-variant px-6"
      style={{ height: 56, left: 240 }}
    >
      {/* Breadcrumb */}
      <nav className="flex items-center gap-1" aria-label="Breadcrumb">
        {crumbs.map((crumb, i) => (
          <React.Fragment key={i}>
            {i > 0 && (
              <ChevronRight size={13} className="text-outline-variant" strokeWidth={2} />
            )}
            {crumb.to && i < crumbs.length - 1 ? (
              <Link
                to={crumb.to}
                className="text-[13px] text-on-surface-variant hover:text-on-surface transition-colors"
              >
                {crumb.label}
              </Link>
            ) : (
              <span
                className={`text-[13px] ${
                  i === crumbs.length - 1
                    ? 'text-on-surface font-medium'
                    : 'text-on-surface-variant'
                }`}
              >
                {crumb.label}
              </span>
            )}
          </React.Fragment>
        ))}
      </nav>

      {/* Actions */}
      <div className="flex items-center gap-1">
        <Button variant="ghost" size="sm" aria-label="Notificaciones" className="w-8 h-8 p-0">
          <Bell size={16} strokeWidth={1.8} />
        </Button>
        <Button variant="ghost" size="sm" aria-label="Configuración" className="w-8 h-8 p-0">
          <Settings size={16} strokeWidth={1.8} />
        </Button>
      </div>
    </header>
  )
}
