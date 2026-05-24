import React, { useEffect, useState, useCallback } from 'react'
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  RefreshCw,
  Activity,
  Database,
  Wifi,
  Loader2,
} from 'lucide-react'
import { Card, CardHeader } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { getBitacora, getFuentes, postIngesta, type BitacoraEntry, type Fuente } from '@/lib/api'
import { cn, relativeTime } from '@/lib/utils'

// ─── Status icon helper ───────────────────────────────────────────────────────

const StatusIcon: React.FC<{ estado: string; size?: number }> = ({ estado, size = 16 }) => {
  if (estado === 'ok')
    return <CheckCircle2 size={size} className="text-emerald-600 shrink-0" strokeWidth={2} />
  if (estado === 'warn')
    return <AlertTriangle size={size} className="text-amber-500 shrink-0" strokeWidth={2} />
  return <XCircle size={size} className="text-error shrink-0" strokeWidth={2} />
}

// ─── Stat card ────────────────────────────────────────────────────────────────

interface StatCardProps {
  icon: React.ElementType
  title: string
  value: string
  subtitle?: string
  iconColor?: string
}

const StatCard: React.FC<StatCardProps> = ({
  icon: Icon,
  title,
  value,
  subtitle,
  iconColor = 'text-primary-container',
}) => (
  <Card className="flex items-start gap-4">
    <div className="w-10 h-10 rounded-btn bg-surface-container-low border border-outline-variant flex items-center justify-center shrink-0">
      <Icon size={18} strokeWidth={2} className={iconColor} />
    </div>
    <div className="min-w-0">
      <p className="label-caps text-on-surface-variant mb-1">{title}</p>
      <p className="text-[20px] font-bold text-on-surface leading-tight">{value}</p>
      {subtitle && (
        <p className="text-[12px] text-on-surface-variant mt-0.5">{subtitle}</p>
      )}
    </div>
  </Card>
)

// ─── Enriched fuente type (augmented with latest bitacora entry) ──────────────

interface FuenteEnriquecida extends Fuente {
  estado: string
  ultimo_ingesta_fecha?: string
  registros_ok?: number
  rechazos?: number
  mensaje_reciente?: string
}

function enrichFuentes(fuentes: Fuente[], entries: BitacoraEntry[]): FuenteEnriquecida[] {
  return fuentes.map((f) => {
    const fuenteEntries = entries
      .filter((e) => e.fuente === f.nombre)
      .sort((a, b) => new Date(b.fecha).getTime() - new Date(a.fecha).getTime())
    const latest = fuenteEntries[0]
    return {
      ...f,
      estado: latest?.estado ?? 'ok',
      ultimo_ingesta_fecha: latest?.fecha ?? f.ultima_ingesta,
      registros_ok: latest?.registros_ingestados,
      rechazos: latest?.registros_rechazados,
      mensaje_reciente: latest?.mensaje ?? undefined,
    }
  })
}

// ─── Main page ────────────────────────────────────────────────────────────────

export const Bitacora: React.FC = () => {
  const [entries, setEntries] = useState<BitacoraEntry[]>([])
  const [fuentes, setFuentes] = useState<FuenteEnriquecida[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [retrying, setRetrying] = useState<Set<string>>(new Set())
  const [error, setError] = useState<string | null>(null)

  const loadData = useCallback(async (showRefresh = false) => {
    if (showRefresh) setRefreshing(true)
    else setLoading(true)
    setError(null)

    try {
      const [bitacoraData, fuentesData] = await Promise.all([
        getBitacora(20),
        getFuentes(),
      ])
      const items = bitacoraData.items
      setEntries(items)
      setFuentes(enrichFuentes(fuentesData, items))
    } catch {
      setError('No se pudo cargar la bitácora. Verifique su conexión con el servidor.')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  const handleReintentar = async (fuente: string) => {
    setRetrying((prev) => new Set(prev).add(fuente))
    try {
      await postIngesta(fuente)
      await loadData(true)
    } catch {
      // silently fail — could show toast in production
    } finally {
      setRetrying((prev) => {
        const next = new Set(prev)
        next.delete(fuente)
        return next
      })
    }
  }

  // ─── Derived stats ──────────────────────────────────────────────────────────

  const totalRegistros = entries.reduce((sum, e) => sum + (e.registros_ingestados ?? 0), 0)
  const fuentesOk = fuentes.filter((f) => f.estado === 'ok').length
  const totalFuentes = fuentes.length

  // ─── Alerts from bitácora ──────────────────────────────────────────────────

  const errorEntries = entries.filter((e) => e.estado === 'error')
  const warnEntries = entries.filter((e) => e.estado === 'warn')

  if (loading) {
    return (
      <div className="max-w-5xl space-y-6 animate-pulse">
        <div className="h-8 w-48 bg-outline-variant rounded" />
        <div className="grid grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-24 bg-outline-variant/40 rounded-card" />
          ))}
        </div>
        <div className="h-64 bg-outline-variant/40 rounded-card" />
      </div>
    )
  }

  return (
    <div className="max-w-5xl space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Activity size={20} className="text-primary-container" strokeWidth={2} />
            <h1 className="text-[24px] font-bold text-on-surface tracking-tight">
              Bitácora de Ingesta
            </h1>
          </div>
          <p className="text-[14px] text-on-surface-variant">
            Monitor de operaciones de sincronización de fuentes de datos.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => loadData(true)}
          loading={refreshing}
        >
          {!refreshing && <RefreshCw size={14} strokeWidth={2} />}
          Actualizar
        </Button>
      </div>

      {/* Error */}
      {error && (
        <div className="p-3 rounded-card border border-red-200 bg-red-50 text-[13px] text-error">
          {error}
        </div>
      )}

      {/* Stats row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard
          icon={Database}
          title="Volumen procesado"
          value={totalRegistros.toLocaleString('es-CO')}
          subtitle="registros ingestados (últimas 20 ops)"
          iconColor="text-primary-container"
        />
        <StatCard
          icon={Wifi}
          title="Salud de fuentes"
          value={`${fuentesOk} de ${totalFuentes || '—'}`}
          subtitle={
            totalFuentes > 0
              ? `${Math.round((fuentesOk / totalFuentes) * 100)}% operando correctamente`
              : 'Sin fuentes registradas'
          }
          iconColor={fuentesOk === totalFuentes ? 'text-emerald-600' : 'text-amber-500'}
        />
        <StatCard
          icon={RefreshCw}
          title="Sincronización"
          value="Activo"
          subtitle="Próxima: en 45 min"
          iconColor="text-emerald-600"
        />
      </div>

      {/* Fuentes monitoring table */}
      {fuentes.length > 0 && (
        <Card padding={false} className="overflow-hidden">
          <div className="px-5 py-3.5 border-b border-outline-variant bg-surface-container-low">
            <h2 className="text-[14px] font-semibold text-on-surface">Monitor de fuentes</h2>
            <p className="text-[12px] text-on-surface-variant mt-0.5">
              Estado en tiempo real de cada fuente de datos registrada
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-[13px]">
              <thead>
                <tr className="border-b border-outline-variant">
                  <th className="text-left px-5 py-2.5 label-caps text-on-surface-variant">Fuente</th>
                  <th className="text-left px-5 py-2.5 label-caps text-on-surface-variant">Última ingesta</th>
                  <th className="text-left px-5 py-2.5 label-caps text-on-surface-variant">Estado</th>
                  <th className="text-right px-5 py-2.5 label-caps text-on-surface-variant">Reg. OK</th>
                  <th className="text-right px-5 py-2.5 label-caps text-on-surface-variant">Rechazos</th>
                  <th className="text-left px-5 py-2.5 label-caps text-on-surface-variant">Mensaje</th>
                  <th className="px-5 py-2.5" />
                </tr>
              </thead>
              <tbody>
                {fuentes.map((fuente) => {
                  const isRetrying = retrying.has(fuente.nombre)
                  const needsAction = fuente.estado === 'warn' || fuente.estado === 'error'
                  return (
                    <tr
                      key={fuente.nombre}
                      className={cn(
                        'border-b border-outline-variant last:border-0 transition-colors',
                        fuente.estado === 'error'
                          ? 'bg-red-50/50'
                          : fuente.estado === 'warn'
                          ? 'bg-amber-50/50'
                          : 'hover:bg-surface-container-low',
                      )}
                    >
                      <td className="px-5 py-3">
                        <div className="flex items-center gap-2">
                          <div className="w-6 h-6 rounded bg-surface-container-low border border-outline-variant flex items-center justify-center">
                            <Database size={12} className="text-outline" />
                          </div>
                          <span className="font-semibold text-on-surface">{fuente.nombre}</span>
                        </div>
                      </td>
                      <td className="px-5 py-3 text-on-surface-variant">
                        {fuente.ultimo_ingesta_fecha ? relativeTime(fuente.ultimo_ingesta_fecha) : '—'}
                      </td>
                      <td className="px-5 py-3">
                        <div className="flex items-center gap-1.5">
                          <StatusIcon estado={fuente.estado} size={15} />
                          <span
                            className={cn(
                              'text-[12px] font-semibold capitalize',
                              fuente.estado === 'ok'
                                ? 'text-emerald-700'
                                : fuente.estado === 'warn'
                                ? 'text-amber-700'
                                : 'text-error',
                            )}
                          >
                            {fuente.estado}
                          </span>
                        </div>
                      </td>
                      <td className="px-5 py-3 text-right font-mono text-[12px] text-emerald-700 font-semibold">
                        {(fuente.registros_ok ?? 0).toLocaleString('es-CO')}
                      </td>
                      <td className="px-5 py-3 text-right font-mono text-[12px]">
                        <span className={fuente.rechazos ? 'text-error font-semibold' : 'text-on-surface-variant'}>
                          {(fuente.rechazos ?? 0).toLocaleString('es-CO')}
                        </span>
                      </td>
                      <td className="px-5 py-3 max-w-[180px]">
                        <span className="text-[12px] text-on-surface-variant truncate block">
                          {fuente.mensaje_reciente ?? '—'}
                        </span>
                      </td>
                      <td className="px-5 py-3">
                        <Button
                          variant={needsAction ? 'primary' : 'ghost'}
                          size="sm"
                          loading={isRetrying}
                          onClick={() => handleReintentar(fuente.nombre)}
                        >
                          {!isRetrying && <RefreshCw size={12} strokeWidth={2} />}
                          Reintentar
                        </Button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Alerts section */}
      {(errorEntries.length > 0 || warnEntries.length > 0) && (
        <div>
          <h2 className="text-[15px] font-semibold text-on-surface mb-3">Alertas activas</h2>
          <div className="space-y-2">
            {errorEntries.map((entry) => (
              <div
                key={entry.id}
                className="flex items-start gap-3 p-4 rounded-card border border-red-200 bg-red-50"
              >
                <XCircle size={16} className="text-error shrink-0 mt-0.5" strokeWidth={2} />
                <div className="min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-[13px] font-semibold text-red-800">{entry.fuente}</span>
                    <span className="text-[11px] text-red-500">
                      {entry.fecha ? relativeTime(entry.fecha) : ''}
                    </span>
                  </div>
                  <p className="text-[13px] text-red-700">
                    {entry.mensaje ?? 'Error durante la ingesta'}
                  </p>
                  <p className="text-[11px] text-red-500 mt-0.5">
                    {entry.registros_rechazados} rechazos · {entry.registros_ingestados} procesados
                  </p>
                </div>
              </div>
            ))}
            {warnEntries.map((entry) => (
              <div
                key={entry.id}
                className="flex items-start gap-3 p-4 rounded-card border border-amber-200 bg-amber-50"
              >
                <AlertTriangle size={16} className="text-amber-600 shrink-0 mt-0.5" strokeWidth={2} />
                <div className="min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-[13px] font-semibold text-amber-800">{entry.fuente}</span>
                    <span className="text-[11px] text-amber-500">
                      {entry.fecha ? relativeTime(entry.fecha) : ''}
                    </span>
                  </div>
                  <p className="text-[13px] text-amber-700">
                    {entry.mensaje ?? 'Advertencia durante la ingesta'}
                  </p>
                  <p className="text-[11px] text-amber-500 mt-0.5">
                    {entry.registros_rechazados} rechazos · {entry.registros_ingestados} procesados
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Bitácora log table */}
      <Card padding={false} className="overflow-hidden">
        <CardHeader
          title="Registro de operaciones"
          subtitle={`Últimas ${entries.length} operaciones de ingesta`}
          className="px-5 pt-4 pb-0 mb-0 border-b border-outline-variant pb-3"
        />
        {entries.length === 0 ? (
          <div className="py-12 text-center text-on-surface-variant text-[14px]">
            No hay operaciones registradas.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-[13px]">
              <thead>
                <tr className="border-b border-outline-variant bg-surface-container-low">
                  <th className="text-left px-5 py-2.5 label-caps text-on-surface-variant">Fuente</th>
                  <th className="text-left px-5 py-2.5 label-caps text-on-surface-variant">Inicio</th>
                  <th className="text-left px-5 py-2.5 label-caps text-on-surface-variant">Estado</th>
                  <th className="text-right px-5 py-2.5 label-caps text-on-surface-variant">Ingestados</th>
                  <th className="text-right px-5 py-2.5 label-caps text-on-surface-variant">Rechazos</th>
                  <th className="text-left px-5 py-2.5 label-caps text-on-surface-variant">Mensaje</th>
                </tr>
              </thead>
              <tbody>
                {entries.map((entry) => (
                  <tr
                    key={entry.id}
                    className="border-b border-outline-variant last:border-0 hover:bg-surface-container-low transition-colors"
                  >
                    <td className="px-5 py-3 font-semibold text-on-surface">{entry.fuente}</td>
                    <td className="px-5 py-3 text-on-surface-variant">
                      {entry.fecha ? relativeTime(entry.fecha) : '—'}
                    </td>
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-1.5">
                        <StatusIcon estado={entry.estado} size={14} />
                        <span
                          className={cn(
                            'text-[12px] font-semibold capitalize',
                            entry.estado === 'ok'
                              ? 'text-emerald-700'
                              : entry.estado === 'warn'
                              ? 'text-amber-700'
                              : 'text-error',
                          )}
                        >
                          {entry.estado}
                        </span>
                      </div>
                    </td>
                    <td className="px-5 py-3 text-right font-mono text-[12px] text-emerald-700 font-semibold">
                      {entry.registros_ingestados.toLocaleString('es-CO')}
                    </td>
                    <td className="px-5 py-3 text-right font-mono text-[12px]">
                      <span className={entry.registros_rechazados > 0 ? 'text-error font-semibold' : 'text-on-surface-variant'}>
                        {entry.registros_rechazados.toLocaleString('es-CO')}
                      </span>
                    </td>
                    <td className="px-5 py-3 max-w-[200px]">
                      <span className="text-[12px] text-on-surface-variant truncate block">
                        {entry.mensaje ?? '—'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}
