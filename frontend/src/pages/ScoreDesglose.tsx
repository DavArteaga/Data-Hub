import React, { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { AlertTriangle, CheckCircle2, AlertCircle, TrendingUp, Layers, Clock, Star } from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { ScoreBar } from '@/components/ui/ScoreBar'
import { ScoreCircle } from '@/components/ui/ScoreCircle'
import { getEmpresaScore, getEmpresa, type EmpresaScore, type IndicadorScore, type EmpresaDetail } from '@/lib/api'
import { cn, formatValue, scoreColor } from '@/lib/utils'

// ─── Skeleton ─────────────────────────────────────────────────────────────────

const Skeleton = () => (
  <div className="space-y-6 max-w-5xl animate-pulse">
    <div className="space-y-2">
      <div className="h-6 w-64 bg-outline-variant rounded" />
      <div className="h-4 w-40 bg-outline-variant/60 rounded" />
    </div>
    <div className="h-24 bg-outline-variant/40 rounded-card" />
    <div className="grid grid-cols-3 gap-4">
      {[...Array(3)].map((_, i) => (
        <div key={i} className="h-32 bg-outline-variant/40 rounded-card" />
      ))}
    </div>
    <div className="h-48 bg-outline-variant/40 rounded-card" />
  </div>
)

// ─── Formula Card ─────────────────────────────────────────────────────────────

interface FormulaCardProps {
  indicador: IndicadorScore
  descripcion: string
}

const FormulaCard: React.FC<FormulaCardProps> = ({ indicador, descripcion }) => {
  const { desglose } = indicador
  const calc = indicador.score_final.toFixed(3)

  return (
    <Card className="border-primary-container/20 bg-gradient-to-br from-surface to-surface-container-low">
      <div className="flex items-start justify-between mb-4">
        <div>
          <p className="label-caps text-primary-container mb-1">Metodología de cálculo</p>
          <h2 className="text-[16px] font-semibold text-on-surface">
            {descripcion}
          </h2>
        </div>
        <ScoreCircle score={indicador.score_final} size={72} label="" showLabel={false} />
      </div>

      {/* Formula */}
      <div className="rounded-btn border border-outline-variant bg-surface-container-low px-4 py-3 mb-4">
        <p className="font-mono text-[12px] text-on-surface-variant mb-1">// fórmula de confiabilidad</p>
        <p className="font-mono text-[14px] text-on-surface">
          score = 0.3×completitud + 0.3×actualidad + 0.4×tier_fuente
        </p>
      </div>

      {/* Calculation */}
      <div className="rounded-btn border border-primary-container/20 bg-primary-container/5 px-4 py-3">
        <p className="label-caps text-primary-container/70 mb-1.5">Aplicado</p>
        <p className="font-mono text-[15px] font-semibold text-on-surface">
          <span className="text-on-surface-variant">0.3×</span>
          <span className={scoreColor(desglose.completitud).text}>
            {desglose.completitud.toFixed(2)}
          </span>
          <span className="text-on-surface-variant mx-1.5">+</span>
          <span className="text-on-surface-variant">0.3×</span>
          <span className={scoreColor(desglose.actualidad).text}>
            {desglose.actualidad.toFixed(2)}
          </span>
          <span className="text-on-surface-variant mx-1.5">+</span>
          <span className="text-on-surface-variant">0.4×</span>
          <span className={scoreColor(desglose.tier_fuente).text}>
            {desglose.tier_fuente.toFixed(2)}
          </span>
          <span className="text-on-surface-variant mx-1.5">=</span>
          <span className={cn('font-bold', scoreColor(indicador.score_final).text)}>
            {calc}
          </span>
        </p>
      </div>
    </Card>
  )
}

// ─── Factor Cards ─────────────────────────────────────────────────────────────

interface FactorCardProps {
  icon: React.ElementType
  title: string
  subtitle: string
  value: number
  weight: string
}

const FactorCard: React.FC<FactorCardProps> = ({ icon: Icon, title, subtitle, value, weight }) => {
  const { hex, text } = scoreColor(value)
  return (
    <Card className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div
            className="w-8 h-8 rounded-btn flex items-center justify-center"
            style={{ backgroundColor: hex + '18' }}
          >
            <Icon size={16} strokeWidth={2} style={{ color: hex }} />
          </div>
          <span className="text-[13px] font-semibold text-on-surface">{title}</span>
        </div>
        <span className="label-caps text-on-surface-variant/60">{weight}</span>
      </div>

      <div>
        <span className={cn('text-[28px] font-bold leading-none', text)}>
          {Math.round(value * 100)}
        </span>
        <span className="text-[14px] text-on-surface-variant ml-1">/100</span>
      </div>

      <ScoreBar score={value} showValue={false} height={8} />

      <p className="text-[12px] text-on-surface-variant">{subtitle}</p>
    </Card>
  )
}

// ─── Source Table ─────────────────────────────────────────────────────────────

interface SourceTableProps {
  indicador: IndicadorScore
  descripcion: string
  unidad: string
}

const SourceTable: React.FC<SourceTableProps> = ({ indicador, descripcion, unidad }) => {
  const sorted = [...indicador.fuentes].sort((a, b) => b.tier - a.tier)
  const maxTier = Math.max(...sorted.map((f) => f.tier))

  // Compute diferencia_pct vs the highest-tier source
  const refVal = typeof sorted[0]?.valor === 'number' ? (sorted[0].valor as number) : null
  const withDiff = sorted.map((f) => {
    const v = typeof f.valor === 'number' ? (f.valor as number) : null
    const diff =
      v !== null && refVal !== null && refVal !== 0
        ? ((v - refVal) / refVal) * 100
        : null
    return { ...f, diferencia_pct: diff }
  })

  return (
    <Card padding={false} className="overflow-hidden">
      <div className="px-5 py-3.5 border-b border-outline-variant bg-surface-container-low">
        <h3 className="text-[14px] font-semibold text-on-surface">Comparación de fuentes</h3>
        <p className="text-[12px] text-on-surface-variant mt-0.5">
          Valores reportados por cada fuente para {descripcion.toLowerCase()}
        </p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-[13px]">
          <thead>
            <tr className="border-b border-outline-variant">
              <th className="text-left px-5 py-2.5 label-caps text-on-surface-variant">Fuente</th>
              <th className="text-left px-5 py-2.5 label-caps text-on-surface-variant">Tier</th>
              <th className="text-left px-5 py-2.5 label-caps text-on-surface-variant">Valor reportado</th>
              <th className="text-left px-5 py-2.5 label-caps text-on-surface-variant">Diferencia (%)</th>
            </tr>
          </thead>
          <tbody>
            {withDiff.map((fuente, i) => {
              const isTop = fuente.tier === maxTier
              const tierLevel = Math.round(fuente.tier * 5)
              return (
                <tr
                  key={i}
                  className={cn(
                    'border-b border-outline-variant last:border-0 transition-colors',
                    isTop
                      ? 'bg-primary-container/5 border-l-2 border-l-primary-container'
                      : 'hover:bg-surface-container-low',
                  )}
                >
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-2">
                      {isTop && (
                        <Star size={12} className="text-primary-container fill-primary-container" />
                      )}
                      <span className={cn('font-medium', isTop ? 'text-primary-container' : 'text-on-surface')}>
                        {fuente.nombre}
                      </span>
                    </div>
                  </td>
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-1">
                      {[...Array(tierLevel)].map((_, j) => (
                        <div
                          key={j}
                          className={cn(
                            'w-2 h-2 rounded-full',
                            isTop ? 'bg-primary-container' : 'bg-outline',
                          )}
                        />
                      ))}
                      {[...Array(Math.max(0, 5 - tierLevel))].map((_, j) => (
                        <div key={j} className="w-2 h-2 rounded-full bg-outline-variant" />
                      ))}
                    </div>
                  </td>
                  <td className="px-5 py-3 font-mono text-[12px]">
                    {formatValue(fuente.valor, unidad)}
                  </td>
                  <td className="px-5 py-3">
                    {fuente.diferencia_pct !== null ? (
                      <span
                        className={cn(
                          'font-mono text-[12px] font-semibold',
                          Math.abs(fuente.diferencia_pct!) < 5
                            ? 'text-emerald-700'
                            : Math.abs(fuente.diferencia_pct!) < 15
                            ? 'text-amber-700'
                            : 'text-error',
                        )}
                      >
                        {fuente.diferencia_pct! > 0 ? '+' : ''}
                        {fuente.diferencia_pct!.toFixed(1)}%
                      </span>
                    ) : (
                      <span className="text-on-surface-variant">—</span>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </Card>
  )
}

// ─── Consensus Alert ──────────────────────────────────────────────────────────

const ConsensusAlert: React.FC<{ consenso: string }> = ({ consenso }) => {
  const isLow = consenso.includes('Baja divergencia')
  const isMed = consenso.includes('Divergencia media')

  if (isLow) {
    return (
      <div className="flex items-start gap-3 p-4 rounded-card border border-emerald-200 bg-emerald-50">
        <CheckCircle2 size={18} className="text-emerald-600 shrink-0 mt-0.5" strokeWidth={2} />
        <div>
          <p className="text-[13px] font-semibold text-emerald-800 mb-0.5">Consenso de fuentes</p>
          <p className="text-[13px] text-emerald-700">{consenso}</p>
        </div>
      </div>
    )
  }

  if (isMed) {
    return (
      <div className="flex items-start gap-3 p-4 rounded-card border border-amber-200 bg-amber-50">
        <AlertTriangle size={18} className="text-amber-600 shrink-0 mt-0.5" strokeWidth={2} />
        <div>
          <p className="text-[13px] font-semibold text-amber-800 mb-0.5">Consenso de fuentes</p>
          <p className="text-[13px] text-amber-700">{consenso}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex items-start gap-3 p-4 rounded-card border border-red-200 bg-red-50">
      <AlertCircle size={18} className="text-error shrink-0 mt-0.5" strokeWidth={2} />
      <div>
        <p className="text-[13px] font-semibold text-red-800 mb-0.5">Consenso de fuentes</p>
        <p className="text-[13px] text-red-700">{consenso}</p>
      </div>
    </div>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export const ScoreDesglose: React.FC = () => {
  const { nit, indicador: indicadorParam } = useParams<{ nit: string; indicador: string }>()
  const [scoreData, setScoreData] = useState<EmpresaScore | null>(null)
  const [empresa, setEmpresa] = useState<EmpresaDetail | null>(null)
  const [activeIndicador, setActiveIndicador] = useState<string>(indicadorParam ?? '')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const decoded = nit ? decodeURIComponent(nit) : ''

  useEffect(() => {
    if (!decoded) return
    setLoading(true)
    setError(null)

    Promise.all([getEmpresaScore(decoded), getEmpresa(decoded)])
      .then(([score, emp]) => {
        setScoreData(score)
        setEmpresa(emp)
        if (!activeIndicador && score.indicadores.length > 0) {
          setActiveIndicador(score.indicadores[0].codigo)
        }
      })
      .catch(() => {
        setError('No se pudo cargar el desglose de score. Verifique su conexión.')
      })
      .finally(() => setLoading(false))
  }, [decoded])

  if (loading) return <Skeleton />

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-24 gap-4">
        <AlertCircle size={40} className="text-error" />
        <p className="text-[14px] text-on-surface-variant text-center max-w-sm">{error}</p>
        <Link to="/" className="text-[13px] text-primary-container hover:underline">
          ← Volver al inicio
        </Link>
      </div>
    )
  }

  if (!scoreData) return null

  const indicadorData: IndicadorScore | undefined =
    scoreData.indicadores.find((i) => i.codigo === activeIndicador) ??
    scoreData.indicadores[0]

  if (!indicadorData) {
    return (
      <div className="text-center py-24 text-on-surface-variant">
        No hay datos de score disponibles para esta empresa.
      </div>
    )
  }

  // Enrich with metadata from empresa detail
  const detalle = empresa?.indicadores.find((i) => i.codigo === indicadorData.codigo)
  const descripcion = detalle?.descripcion ?? indicadorData.codigo
  const unidad = detalle?.unidad ?? ''
  const periodo = detalle?.periodo ?? '2024'

  return (
    <div className="max-w-5xl space-y-6">
      {/* Breadcrumb header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-[24px] font-bold text-on-surface tracking-tight leading-tight">
            {scoreData.razon_social}
          </h1>
          <div className="flex items-center gap-3 mt-1.5">
            <span className="font-mono text-[12px] text-on-surface-variant bg-surface-container-low px-2 py-0.5 rounded border border-outline-variant">
              {scoreData.nit}
            </span>
            <span className="text-on-surface-variant text-[12px]">/</span>
            <span className="text-[13px] font-semibold text-primary-container">
              Score · {indicadorData.codigo}
            </span>
          </div>
        </div>
        <Link
          to={`/empresas/${encodeURIComponent(decoded)}`}
          className="text-[13px] text-on-surface-variant hover:text-on-surface hover:underline shrink-0 mt-1"
        >
          ← Volver a detalle
        </Link>
      </div>

      {/* Indicator tabs */}
      {scoreData.indicadores.length > 1 && (
        <div className="flex gap-1 p-1 bg-surface-container-low rounded-card border border-outline-variant w-fit">
          {scoreData.indicadores.map((ind) => (
            <button
              key={ind.codigo}
              onClick={() => setActiveIndicador(ind.codigo)}
              className={cn(
                'px-4 py-1.5 rounded-btn text-[13px] font-medium transition-colors',
                activeIndicador === ind.codigo
                  ? 'bg-primary-container text-white shadow-sm'
                  : 'text-on-surface-variant hover:text-on-surface hover:bg-white/60',
              )}
            >
              {ind.codigo}
            </button>
          ))}
        </div>
      )}

      {/* Formula card */}
      <FormulaCard indicador={indicadorData} descripcion={descripcion} />

      {/* Factor mini-cards */}
      <div className="grid grid-cols-3 gap-4">
        <FactorCard
          icon={Layers}
          title="Completitud"
          subtitle="Completitud de campos declarados"
          value={indicadorData.desglose.completitud}
          weight="30%"
        />
        <FactorCard
          icon={Clock}
          title="Actualidad"
          subtitle="Actualidad del dato reportado"
          value={indicadorData.desglose.actualidad}
          weight="30%"
        />
        <FactorCard
          icon={TrendingUp}
          title="Tier de fuente"
          subtitle="Confiabilidad de la fuente"
          value={indicadorData.desglose.tier_fuente}
          weight="40%"
        />
      </div>

      {/* Consensus alert */}
      {indicadorData.consenso && <ConsensusAlert consenso={indicadorData.consenso} />}

      {/* Source comparison table */}
      {indicadorData.fuentes.length > 0 && (
        <SourceTable indicador={indicadorData} descripcion={descripcion} unidad={unidad} />
      )}

      {/* Global score context */}
      <Card className="flex items-center gap-5 border-outline-variant/80">
        <div className="shrink-0">
          <ScoreCircle
            score={scoreData.score_global}
            size={72}
            showLabel={false}
          />
        </div>
        <div>
          <p className="label-caps text-on-surface-variant mb-1">Score global del portafolio</p>
          <p className="text-[22px] font-bold text-on-surface leading-none">
            {Math.round(scoreData.score_global * 100)}/100
          </p>
          <p className="text-[12px] text-on-surface-variant mt-1">
            Promedio ponderado de {scoreData.indicadores.length} indicadores — período {periodo}
          </p>
        </div>
        <div className="flex-1 ml-4 space-y-2">
          {scoreData.indicadores.map((ind) => (
            <div key={ind.codigo} className="flex items-center gap-3">
              <span
                className={cn(
                  'text-[11px] font-semibold w-20 truncate shrink-0',
                  ind.codigo === activeIndicador
                    ? 'text-primary-container'
                    : 'text-on-surface-variant',
                )}
              >
                {ind.codigo}
              </span>
              <ScoreBar
                score={ind.score_final}
                showValue={true}
                height={5}
                className="flex-1"
              />
            </div>
          ))}
        </div>
      </Card>

      {/* Back */}
      <div className="pb-4">
        <Link
          to={`/empresas/${encodeURIComponent(decoded)}`}
          className="text-[13px] text-on-surface-variant hover:text-on-surface hover:underline"
        >
          ← Volver a detalle de empresa
        </Link>
      </div>
    </div>
  )
}
