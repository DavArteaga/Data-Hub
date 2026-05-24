import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1'

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 15_000,
  headers: { 'Content-Type': 'application/json' },
})

// ─── Response Types ────────────────────────────────────────────────────────────

// List endpoint
export interface Empresa {
  nit: string
  razon_social: string
  ciiu_principal: string
  estado: string
  score_global: number
}

export interface EmpresaListResponse {
  page: number
  size: number
  total: number
  filtros_aplicados: Record<string, string>
  items: Empresa[]
}

// Detail endpoint
export interface EmpresaIndicador {
  codigo: string
  descripcion: string
  valor: number | string
  unidad: string
  periodo: string
  score: number
  fuente_principal: string
}

export interface EmpresaDetail {
  nit: string
  razon_social: string
  ciiu_principal: string
  ciiu_secundarios: string[]
  estado: string
  fecha_constitucion?: string
  fuentes_consultadas: string[]
  score_global: number
  indicadores: EmpresaIndicador[]
}

// Score endpoint
export interface ScoreBreakdown {
  completitud: number
  actualidad: number
  tier_fuente: number
  calculo: string
}

export interface ScoreFuente {
  nombre: string
  valor: number | string
  tier: number
}

export interface IndicadorScore {
  codigo: string
  score_final: number
  desglose: ScoreBreakdown
  fuentes: ScoreFuente[]
  consenso: string
}

export interface EmpresaScore {
  nit: string
  razon_social: string
  score_global: number
  formula?: string
  indicadores: IndicadorScore[]
}

// Historico endpoint
export interface HistoricoItem {
  periodo: string
  valor: number | string
  score: number
  fuente: string
}

export interface HistoricoResponse {
  nit: string
  indicador: string
  descripcion: string
  unidad: string
  serie: HistoricoItem[]
}

// Indicadores endpoint
export interface Indicador {
  id: number
  codigo: string
  descripcion: string
  unidad: string
}

// Fuentes endpoint
export interface Fuente {
  id: number
  nombre: string
  url_base?: string
  tipo: string
  tier: number
  ultima_ingesta?: string
}

// Bitácora endpoint
export interface BitacoraEntry {
  id: number
  fuente: string
  fecha: string
  registros_ingestados: number
  registros_rechazados: number
  estado: 'ok' | 'warn' | 'error' | string
  mensaje?: string
}

export interface BitacoraResponse {
  items: BitacoraEntry[]
}

// Ingesta endpoint
export interface IngestaResult {
  fuente: string
  estado: string
  registros_ingestados: number
  registros_rechazados: number
  mensaje?: string
}

// ─── Query Params ──────────────────────────────────────────────────────────────

export interface EmpresaParams {
  ciiu?: string
  page?: number
  size?: number
}

// ─── API Functions ─────────────────────────────────────────────────────────────

/** GET /empresas — list companies with optional filters */
export async function getEmpresas(params: EmpresaParams = {}): Promise<EmpresaListResponse> {
  const { data } = await client.get<EmpresaListResponse>('/empresas', { params })
  return data
}

/** GET /empresas/:nit — single company detail */
export async function getEmpresa(nit: string): Promise<EmpresaDetail> {
  const { data } = await client.get<EmpresaDetail>(`/empresas/${encodeURIComponent(nit)}`)
  return data
}

/** GET /empresas/:nit/score?indicador=X — score breakdown for a company */
export async function getEmpresaScore(nit: string, indicador?: string): Promise<EmpresaScore> {
  const params = indicador ? { indicador } : {}
  const { data } = await client.get<EmpresaScore>(
    `/empresas/${encodeURIComponent(nit)}/score`,
    { params },
  )
  return data
}

/** GET /empresas/:nit/historico?indicador=X — time-series data */
export async function getEmpresaHistorico(nit: string, indicador: string): Promise<HistoricoResponse> {
  const { data } = await client.get<HistoricoResponse>(
    `/empresas/${encodeURIComponent(nit)}/historico`,
    { params: { indicador } },
  )
  return data
}

/** GET /indicadores — reference list of indicators */
export async function getIndicadores(): Promise<Indicador[]> {
  const { data } = await client.get<Indicador[]>('/indicadores')
  return data
}

/** GET /fuentes — list of data sources */
export async function getFuentes(): Promise<Fuente[]> {
  const { data } = await client.get<Fuente[]>('/fuentes')
  return data
}

/** GET /bitacora?limit=N — ingestion log */
export async function getBitacora(limit = 20): Promise<BitacoraResponse> {
  const { data } = await client.get<BitacoraResponse>('/bitacora', { params: { limit } })
  return data
}

/** POST /ingesta/:fuente_nombre — trigger manual ingestion */
export async function postIngesta(fuente: string): Promise<IngestaResult> {
  const { data } = await client.post<IngestaResult>(`/ingesta/${encodeURIComponent(fuente)}`)
  return data
}
