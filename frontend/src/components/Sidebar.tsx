import React from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { Database, Search, Code2, Activity } from 'lucide-react'
import { cn } from '@/lib/utils'

interface NavItem {
  label: string
  icon: React.ElementType
  to: string
  exact?: boolean
}

const navItems: NavItem[] = [
  { label: 'Buscar Empresas', icon: Search, to: '/', exact: true },
  { label: 'API Explorer', icon: Code2, to: '/api-explorer' },
  { label: 'Bitácora', icon: Activity, to: '/bitacora' },
]

export const Sidebar: React.FC = () => {
  const location = useLocation()

  const isActive = (item: NavItem) => {
    if (item.exact) return location.pathname === item.to
    return location.pathname.startsWith(item.to)
  }

  return (
    <aside
      className="fixed left-0 top-0 h-full z-30 flex flex-col bg-surface border-r border-outline-variant"
      style={{ width: 240 }}
    >
      {/* Logo area */}
      <div className="flex items-center gap-3 px-5 py-4 border-b border-outline-variant" style={{ height: 56 }}>
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary-container text-white shrink-0">
          <Database size={16} strokeWidth={2} />
        </div>
        <div className="min-w-0">
          <p className="text-[14px] font-bold text-on-surface leading-tight truncate">DataCore Hub</p>
          <p className="text-[11px] text-on-surface-variant leading-tight truncate">Observatorio TIC</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-3 px-3">
        <p className="label-caps text-on-surface-variant/60 px-2 mb-2 tracking-widest">Navegación</p>
        <ul className="space-y-0.5">
          {navItems.map((item) => {
            const active = isActive(item)
            const Icon = item.icon
            return (
              <li key={item.to}>
                <NavLink
                  to={item.to}
                  className={cn(
                    'flex items-center gap-3 px-3 py-2.5 rounded-md text-[14px] font-medium transition-colors duration-100 relative group',
                    active
                      ? 'bg-surface-container-low text-primary-container font-semibold'
                      : 'text-on-surface-variant hover:bg-surface-container-low hover:text-on-surface',
                  )}
                >
                  {active && (
                    <span
                      className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 rounded-r-full bg-primary-container"
                      style={{ height: '60%' }}
                    />
                  )}
                  <Icon
                    size={17}
                    strokeWidth={active ? 2.2 : 1.8}
                    className={cn(active ? 'text-primary-container' : 'text-outline')}
                  />
                  <span className="truncate">{item.label}</span>
                </NavLink>
              </li>
            )
          })}
        </ul>
      </nav>

      {/* Footer */}
      <div className="px-5 py-3 border-t border-outline-variant">
        <p className="label-caps text-on-surface-variant/50 text-[10px]">
          Softline S.A. · DataCore
        </p>
        <p className="text-[11px] text-on-surface-variant/40 mt-0.5">v2.4.1</p>
      </div>
    </aside>
  )
}
