import React, { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { CheckCircle2, ArrowRight, AlertCircle, Building2 } from 'lucide-react'
import { Card, CardHeader } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { ScoreCircle } from '@/components/ui/ScoreCircle'
import { ScoreBar } from '@/components/ui/ScoreBar'
import { getEmpresa, type EmpresaDetail, type EmpresaIndicador } from '@/lib/api'
import { formatValue } from '@/lib/utils'

const SkeletonCard = () => (
  <Card>
    <div className="space-y-3">
      <div className="skeleton h-4 w-32 rounded" />
      <div className="skeleton h-8 w-48 rounded" />
      <div className="skeleton h-3 w-24 rounded" />
    </div>
  </Card>
)

const SkeletonDetail = () => (
  <div className="space-y-6">
    <div className="space-y-2">
      <div className="skeleton h-8 w-64 rounded" />
      <div className="skeleton h-4 w-40 rounded" />
    </div>
    <div className="grid grid-cols-3 gap-4">
      <SkeletonCard />
      <SkeletonCard />
      <SkeletonCard />
    </div>
  </div>
)

interface MetricCardProps {
  indicador: EmpresaIndicador
  nit: string
}

const MetricCard: React.FC<MetricCardProps> = ({ indicador, nit }) => {
  const formattedValue = formatValue(indicador.valor, indicador.unidad)

  return (
    <Card className="flex flex-col gap-3">
      <div>
        <p className="label-caps text-on-surface-variant mb-1">
          {indicador.codigo}
        </p>
        <h3 className="text-[13px] font-semibold text-on-surface leading-snug">
          {indicador.descripcion}
        </h3>
      </div>

      <ScoreBar score={indicador.score} showValue={true} height={6} />

      <div>
        <span className="text-[22px] font-bold text-on-surface leading-none">
          {formattedValue}
        </span>
        {indicador.unidad && (
          <span className="text-[12px] text-on-surface-variant ml-1.5">{indicador.unidad}</span>
        )}
      </div>

      <div className="text-[12px] text-on-surface-variant space-y-0.5 mt-auto">
        <p className="font-medium">{indicador.periodo}</p>
        <p className="truncate">Fuente: {indicador.fuente_principal}</p>
      </div>

      <Link
        to={`/empresas/${encodeURIComponent(nit)}/score/${indicador.codigo}`}
        className="flex items-center gap-1.5 text-[12px] font-semibold text-primary-container hover:underline mt-1"
      >
        Ver desglose
        <ArrowRight size={13} strokeWidth={2.5} />
      </Link>
    </Card>
  )
}

export const EmpresaDetalle: React.FC = () => {
  const { nit } = useParams<{ nit: string }>()
  const [empresa, setEmpresa] = useState<EmpresaDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!nit) return
    setLoading(true)
    setError(null)

    const decoded = decodeURIComponent(nit)

    getEmpresa(decoded)
      .then((emp) => setEmpresa(emp))
      .catch(() => {
        setError('No se pudo cargar la información de la empresa. Verifique que el NIT es válido.')
      })
      .finally(() => setLoading(false))
  }, [nit])

  if (loading) {
    return (
      <div>
        <SkeletonDetail />
      </div>
    )
  }

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

  if (!empresa) return null

  const isActiva = empresa.estado === 'Activa'
  const uniqueFuentes = empresa.fuentes_consultadas ?? []

  return (
    <div className="max-w-4xl space-y-8">
      {/* Company header */}
      <div>
        <div className="flex items-start gap-4">
          <div className="flex items-center justify-center w-12 h-12 rounded-card bg-surface-container-low border border-outline-variant shrink-0">
            <Building2 size={22} className="text-primary-container" strokeWidth={1.8} />
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-[24px] font-bold text-on-surface tracking-tight leading-tight">
              {empresa.razon_social}
            </h1>
            <div className="flex flex-wrap items-center gap-2 mt-2">
              <span className="font-mono text-[13px] text-on-surface-variant bg-surface-container-low px-2 py-0.5 rounded border border-outline-variant">
                {empresa.nit}
              </span>
              {empresa.ciiu_principal && (
                <Badge variant="info">
                  CIIU {empresa.ciiu_principal}
                </Badge>
              )}
              <Badge variant={isActiva ? 'success' : 'error'}>
                {empresa.estado}
              </Badge>
            </div>
          </div>
        </div>
      </div>

      {/* Global score */}
      <Card className="flex items-center gap-8">
        <ScoreCircle
          score={empresa.score_global}
          size={120}
          label="Score global de confiabilidad"
        />
        <div className="flex-1">
          <h2 className="text-[16px] font-semibold text-on-surface mb-1">
            Confiabilidad general
          </h2>
          <p className="text-[13px] text-on-surface-variant mb-4">
            Índice compuesto basado en {empresa.indicadores.length} indicadores del sector TIC.
          </p>
          <div className="space-y-3">
            {empresa.indicadores.map((ind) => (
              <div key={ind.codigo} className="flex items-center gap-3">
                <span className="text-[12px] text-on-surface-variant w-40 truncate shrink-0">
                  {ind.descripcion}
                </span>
                <ScoreBar score={ind.score} showValue={true} height={5} className="flex-1" />
              </div>
            ))}
          </div>
        </div>
      </Card>

      {/* Metric cards */}
      <div>
        <h2 className="text-[16px] font-semibold text-on-surface mb-4">Indicadores</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {empresa.indicadores.map((ind) => (
            <MetricCard key={ind.codigo} indicador={ind} nit={empresa.nit} />
          ))}
        </div>
      </div>

      {/* Sources */}
      {uniqueFuentes.length > 0 && (
        <Card>
          <CardHeader title="Fuentes consultadas" subtitle={`${uniqueFuentes.length} fuentes de datos`} />
          <ul className="space-y-2">
            {uniqueFuentes.map((fuente) => (
              <li key={fuente} className="flex items-center gap-2.5 text-[13px] text-on-surface">
                <CheckCircle2 size={15} className="text-emerald-600 shrink-0" strokeWidth={2} />
                {fuente}
              </li>
            ))}
          </ul>
        </Card>
      )}

      {/* Back link */}
      <div className="pt-2">
        <Link to="/" className="text-[13px] text-on-surface-variant hover:text-on-surface hover:underline">
          ← Volver a inicio
        </Link>
      </div>
    </div>
  )
}
