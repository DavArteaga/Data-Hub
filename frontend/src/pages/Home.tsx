import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Building2, ChevronRight, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { ScoreBar } from '@/components/ui/ScoreBar'
import { getEmpresas, type Empresa } from '@/lib/api'
import { cn } from '@/lib/utils'

const CIIU_OPTIONS = [
  { value: '', label: 'Seleccione una actividad' },
  { value: '6201', label: '6201 — Desarrollo de sistemas' },
  { value: '6202', label: '6202 — Consultoría informática' },
  { value: '6209', label: '6209 — Otras actividades TI' },
]

export const Home: React.FC = () => {
  const navigate = useNavigate()
  const [nit, setNit] = useState('')
  const [ciiu, setCiiu] = useState('')
  const [results, setResults] = useState<Empresa[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (nit.trim()) {
      navigate(`/empresas/${encodeURIComponent(nit.trim())}`)
      return
    }

    if (ciiu) {
      setLoading(true)
      setResults(null)
      try {
        const data = await getEmpresas({ ciiu })
        setResults(data.items)
      } catch (err) {
        setError('No se pudo obtener la lista de empresas. Verifique la conexión con el servidor.')
        setResults([])
      } finally {
        setLoading(false)
      }
    }
  }

  const getEstadoBadgeVariant = (estado: string) => {
    return estado === 'Activa' ? 'success' : 'error'
  }

  return (
    <div className="max-w-2xl">
      {/* Page heading */}
      <div className="mb-8">
        <h1 className="text-[24px] font-bold text-on-surface tracking-tight mb-2">
          Consultar Información
        </h1>
        <p className="text-[14px] text-on-surface-variant leading-relaxed">
          Inicie una consulta rápida utilizando los parámetros oficiales del sector TI en Colombia.
        </p>
      </div>

      {/* Search form */}
      <Card className="mb-6">
        <form onSubmit={handleSubmit} className="space-y-5">
          {/* NIT input */}
          <div>
            <label className="label-caps text-on-surface-variant block mb-1.5">
              NIT de la empresa
            </label>
            <div className="relative">
              <Building2
                size={16}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-outline"
                strokeWidth={1.8}
              />
              <input
                type="text"
                value={nit}
                onChange={(e) => setNit(e.target.value)}
                placeholder="ej: 900111111-1"
                className={cn(
                  'w-full h-10 pl-9 pr-4 rounded-btn border border-outline-variant bg-surface',
                  'text-[14px] text-on-surface placeholder:text-outline',
                  'focus:outline-none focus:ring-2 focus:ring-primary-container/30 focus:border-primary-container',
                  'transition-colors',
                )}
              />
            </div>
          </div>

          {/* Divider */}
          <div className="flex items-center gap-3">
            <div className="flex-1 h-px bg-outline-variant" />
            <span className="label-caps text-on-surface-variant/60 text-[10px]">O BIEN</span>
            <div className="flex-1 h-px bg-outline-variant" />
          </div>

          {/* CIIU select */}
          <div>
            <label className="label-caps text-on-surface-variant block mb-1.5">
              Filtrar por código CIIU
            </label>
            <select
              value={ciiu}
              onChange={(e) => setCiiu(e.target.value)}
              className={cn(
                'w-full h-10 px-3 rounded-btn border border-outline-variant bg-surface',
                'text-[14px] text-on-surface',
                'focus:outline-none focus:ring-2 focus:ring-primary-container/30 focus:border-primary-container',
                'transition-colors cursor-pointer',
                ciiu === '' && 'text-outline',
              )}
            >
              {CIIU_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value} disabled={opt.value === ''}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          {/* Submit */}
          <Button
            type="submit"
            variant="primary"
            size="md"
            loading={loading}
            disabled={!nit.trim() && !ciiu}
            className="w-full"
          >
            {!loading && <Search size={16} strokeWidth={2} />}
            Consultar
          </Button>
        </form>
      </Card>

      {/* Error */}
      {error && (
        <div className="mb-4 p-3 rounded-card border border-red-200 bg-red-50 text-[13px] text-error">
          {error}
        </div>
      )}

      {/* Loading skeleton */}
      {loading && (
        <Card padding={false} className="overflow-hidden">
          <div className="p-4 border-b border-outline-variant">
            <div className="skeleton h-4 w-32 rounded" />
          </div>
          {[...Array(4)].map((_, i) => (
            <div key={i} className="p-4 border-b border-outline-variant last:border-0 flex gap-4">
              <div className="skeleton h-4 w-28 rounded" />
              <div className="skeleton h-4 w-40 rounded" />
              <div className="skeleton h-4 w-16 rounded ml-auto" />
            </div>
          ))}
        </Card>
      )}

      {/* Results table */}
      {!loading && results !== null && results.length === 0 && (
        <div className="text-center py-12 text-on-surface-variant text-[14px]">
          No se encontraron empresas para el CIIU seleccionado.
        </div>
      )}

      {!loading && results && results.length > 0 && (
        <Card padding={false} className="overflow-hidden">
          <div className="px-5 py-3 border-b border-outline-variant flex items-center justify-between">
            <h2 className="text-[14px] font-semibold text-on-surface">
              Resultados — CIIU {ciiu}
            </h2>
            <span className="text-[12px] text-on-surface-variant">{results.length} empresa(s)</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-[13px]">
              <thead>
                <tr className="border-b border-outline-variant bg-surface-container-low">
                  <th className="text-left px-4 py-2.5 label-caps text-on-surface-variant font-semibold">
                    NIT
                  </th>
                  <th className="text-left px-4 py-2.5 label-caps text-on-surface-variant font-semibold">
                    Razón Social
                  </th>
                  <th className="text-left px-4 py-2.5 label-caps text-on-surface-variant font-semibold">
                    CIIU
                  </th>
                  <th className="text-left px-4 py-2.5 label-caps text-on-surface-variant font-semibold">
                    Estado
                  </th>
                  <th className="text-left px-4 py-2.5 label-caps text-on-surface-variant font-semibold">
                    Score
                  </th>
                  <th className="px-4 py-2.5" />
                </tr>
              </thead>
              <tbody>
                {results.map((emp) => (
                  <tr
                    key={emp.nit}
                    onClick={() => navigate(`/empresas/${encodeURIComponent(emp.nit)}`)}
                    className="border-b border-outline-variant last:border-0 hover:bg-surface-container-low cursor-pointer transition-colors group"
                  >
                    <td className="px-4 py-3 font-mono text-[12px] text-on-surface-variant">
                      {emp.nit}
                    </td>
                    <td className="px-4 py-3 font-medium text-on-surface max-w-[200px] truncate">
                      {emp.razon_social}
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant="info">{emp.ciiu_principal}</Badge>
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant={getEstadoBadgeVariant(emp.estado)}>
                        {emp.estado}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 w-32">
                      {emp.score_global != null ? (
                        <ScoreBar score={emp.score_global} showValue={true} height={5} />
                      ) : (
                        <span className="text-on-surface-variant">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <ChevronRight
                        size={16}
                        className="text-outline-variant group-hover:text-primary-container transition-colors"
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Footer metadata */}
      <div className="mt-12 pt-6 border-t border-outline-variant">
        <p className="font-mono text-[11px] text-on-surface-variant/50">
          CORE_ENGINE: v2.4.1 // LAT: 4.7110 // LONG: -74.0721
        </p>
      </div>
    </div>
  )
}
