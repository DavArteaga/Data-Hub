import React from 'react'
import { ExternalLink, Code2, Zap } from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { cn } from '@/lib/utils'

interface Endpoint {
  method: 'GET' | 'POST'
  path: string
  description: string
  params?: string[]
  body?: string
}

const ENDPOINTS: Endpoint[] = [
  {
    method: 'GET',
    path: '/empresas',
    description: 'Listado paginado de empresas con filtros opcionales por CIIU, estado o término de búsqueda.',
    params: ['ciiu', 'estado', 'search', 'page', 'limit'],
  },
  {
    method: 'GET',
    path: '/empresas/{nit}',
    description: 'Información detallada de una empresa identificada por su NIT (Número de Identificación Tributaria).',
    params: ['nit (path)'],
  },
  {
    method: 'GET',
    path: '/empresas/{nit}/score',
    description: 'Score de confiabilidad con desglose por indicador: completitud, actualidad y tier de fuente.',
    params: ['nit (path)', 'indicador (optional)'],
  },
  {
    method: 'GET',
    path: '/empresas/{nit}/historico',
    description: 'Serie de tiempo con valores históricos de un indicador específico para la empresa.',
    params: ['nit (path)', 'indicador (required)'],
  },
  {
    method: 'POST',
    path: '/ingesta/{fuente_nombre}',
    description: 'Dispara manualmente un proceso de ingesta para la fuente de datos especificada.',
    body: '{ } (no body required)',
  },
  {
    method: 'GET',
    path: '/bitacora',
    description: 'Registro de operaciones de ingesta con estado, conteos y mensajes de error.',
    params: ['limit (default: 20)'],
  },
]

const MethodBadge: React.FC<{ method: 'GET' | 'POST' }> = ({ method }) => (
  <span
    className={cn(
      'inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-bold',
      method === 'GET'
        ? 'bg-emerald-100 text-emerald-700 border border-emerald-200'
        : 'bg-blue-100 text-blue-700 border border-blue-200',
    )}
  >
    {method}
  </span>
)

export const ApiExplorer: React.FC = () => {
  const docsUrl = `${import.meta.env.VITE_API_URL?.replace('/api/v1', '') ?? 'http://localhost:8000'}/docs`

  return (
    <div className="max-w-3xl space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <Code2 size={20} className="text-primary-container" strokeWidth={2} />
          <h1 className="text-[24px] font-bold text-on-surface tracking-tight">
            Consola de Desarrollo
          </h1>
        </div>
        <p className="text-[14px] text-on-surface-variant leading-relaxed">
          API REST del Observatorio TIC Colombia — métricas consolidadas de salud empresarial.
        </p>
      </div>

      {/* Docs link */}
      <Card className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-btn bg-primary-container/10 flex items-center justify-center">
            <Zap size={18} className="text-primary-container" strokeWidth={2} />
          </div>
          <div>
            <p className="text-[14px] font-semibold text-on-surface">Swagger UI / OpenAPI</p>
            <p className="text-[12px] text-on-surface-variant">
              Documentación interactiva con todos los esquemas y ejemplos
            </p>
          </div>
        </div>
        <Button
          variant="primary"
          size="sm"
          onClick={() => window.open(docsUrl, '_blank', 'noopener')}
        >
          <ExternalLink size={13} strokeWidth={2} />
          Abrir Docs
        </Button>
      </Card>

      {/* Base URL */}
      <Card className="bg-surface-container-low">
        <p className="label-caps text-on-surface-variant mb-2">URL base</p>
        <div className="flex items-center gap-2">
          <code className="font-mono text-[13px] text-on-surface bg-surface border border-outline-variant rounded px-3 py-1.5 flex-1">
            {import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1'}
          </code>
          <Badge variant="success">v1</Badge>
        </div>
      </Card>

      {/* Endpoints */}
      <div>
        <h2 className="text-[16px] font-semibold text-on-surface mb-3">Endpoints disponibles</h2>
        <div className="space-y-3">
          {ENDPOINTS.map((ep, i) => (
            <Card key={i} className="hover:border-outline transition-colors">
              <div className="flex items-start gap-3 mb-2">
                <MethodBadge method={ep.method} />
                <code className="font-mono text-[13px] text-on-surface font-semibold break-all">
                  {ep.path}
                </code>
              </div>
              <p className="text-[13px] text-on-surface-variant mb-3 ml-0 pl-0">
                {ep.description}
              </p>
              {ep.params && ep.params.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  <span className="label-caps text-on-surface-variant/60 self-center mr-1">
                    params:
                  </span>
                  {ep.params.map((p) => (
                    <code
                      key={p}
                      className="text-[11px] font-mono bg-surface-container-low border border-outline-variant text-on-surface-variant px-2 py-0.5 rounded"
                    >
                      {p}
                    </code>
                  ))}
                </div>
              )}
              {ep.body && (
                <div className="flex items-center gap-2 mt-1">
                  <span className="label-caps text-on-surface-variant/60">body:</span>
                  <code className="text-[11px] font-mono text-on-surface-variant">
                    {ep.body}
                  </code>
                </div>
              )}
            </Card>
          ))}
        </div>
      </div>

      {/* Rate limit */}
      <Card className="flex items-center gap-3 bg-surface-container-low border-dashed">
        <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
        <p className="text-[13px] text-on-surface-variant">
          <span className="font-semibold text-on-surface">1,000 llamadas / minuto</span>
          {' '}— límite de tasa por IP. Autenticación OAuth2 en roadmap Q3 2026.
        </p>
      </Card>

      {/* iframe placeholder */}
      <div className="rounded-card border border-outline-variant overflow-hidden">
        <div className="flex items-center justify-between px-4 py-2.5 bg-surface-container-low border-b border-outline-variant">
          <p className="text-[13px] font-medium text-on-surface">Vista previa — Swagger UI</p>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => window.open(docsUrl, '_blank', 'noopener')}
          >
            <ExternalLink size={13} strokeWidth={2} />
            Pantalla completa
          </Button>
        </div>
        <div className="relative bg-surface-container-low" style={{ height: 320 }}>
          <iframe
            src={docsUrl}
            className="w-full h-full border-0"
            title="Swagger UI"
            sandbox="allow-scripts allow-same-origin"
          />
          {/* Fallback overlay if iframe fails */}
          <div
            className="absolute inset-0 flex flex-col items-center justify-center bg-surface-container-low/80 pointer-events-none"
            style={{ display: 'none' }}
          >
            <Code2 size={32} className="text-outline mb-2" />
            <p className="text-[13px] text-on-surface-variant">
              Inicie el servidor para ver la documentación interactiva
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
