import type {
  AnalisarResponse,
  HistoricoDetalhe,
  HistoricoListResponse,
  Modo,
  StatsResponse,
} from './types'
import { recordError } from './errorStore'

const BASE = process.env.NEXT_PUBLIC_API_URL ?? ''

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  if (!BASE) throw new Error('NEXT_PUBLIC_API_URL não configurada — verifique as variáveis de ambiente da Vercel.')
  const url = `${BASE}${path}`
  const method = init?.method ?? 'GET'
  try {
    const res = await fetch(url, init)
    if (!res.ok) {
      const err = await res.text().catch(() => res.statusText)
      const msg = err || `HTTP ${res.status}`
      recordError(url, method, msg, res.status)
      throw new Error(msg)
    }
    return res.json() as Promise<T>
  } catch (e) {
    if (e instanceof TypeError) recordError(url, method, e)
    throw e
  }
}

export async function analisarArquivos(
  arquivos: File[],
  modo: Modo = 'auto',
  onProgresso?: (msg: string) => void
): Promise<AnalisarResponse> {
  if (!BASE) throw new Error('NEXT_PUBLIC_API_URL não configurada — verifique as variáveis de ambiente da Vercel.')
  const form = new FormData()
  arquivos.forEach((f) => form.append('arquivos', f))
  form.append('modo', modo)

  // POST retorna job_id imediatamente — retry até 3x se Render estiver acordando
  const uploadUrl = `${BASE}/analisar/arquivo`
  let res: Response | undefined
  let lastUploadErr: unknown
  for (let attempt = 0; attempt < 5; attempt++) {
    if (attempt > 0) await new Promise((r) => setTimeout(r, 15000))
    try {
      res = await fetch(uploadUrl, { method: 'POST', body: form })
      break
    } catch (e) {
      lastUploadErr = e
      recordError(uploadUrl, 'POST', e)
    }
  }
  if (!res) throw lastUploadErr
  if (!res.ok) {
    const err = await res.text().catch(() => res.statusText)
    const msg = err || `HTTP ${res.status}`
    recordError(uploadUrl, 'POST', msg, res.status)
    throw new Error(msg)
  }
  const { job_id } = await res.json() as { job_id: string }

  // Polling a cada 3s até o job terminar (até 10 minutos)
  const MAX_MS = 10 * 60 * 1000
  const start = Date.now()
  while (Date.now() - start < MAX_MS) {
    await new Promise((r) => setTimeout(r, 3000))
    const pollUrl = `${BASE}/analisar/job/${job_id}`
    try {
      const poll = await fetch(pollUrl)
      if (!poll.ok) { recordError(pollUrl, 'GET', `HTTP ${poll.status}`, poll.status); continue }
      const job = await poll.json() as { status: string; error?: string; progresso?: string } & AnalisarResponse
      if (job.progresso && onProgresso) onProgresso(job.progresso)
      if (job.status === 'done') return job
      if (job.status === 'error') {
        const msg = job.error ?? 'Erro na análise.'
        recordError(pollUrl, 'GET', msg)
        throw new Error(msg)
      }
    } catch (e) {
      if (e instanceof TypeError) recordError(pollUrl, 'GET', e)
      throw e
    }
  }
  throw new Error('Análise demorou mais de 10 minutos. Tente com menos arquivos.')
}

export async function analisarTexto(
  texto: string,
  numDocs = 1,
  modo: Modo = 'auto'
): Promise<AnalisarResponse> {
  return request<AnalisarResponse>('/analisar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ texto, num_docs: numDocs, modo }),
  })
}

export async function importarArquivos(arquivos: File[]): Promise<{ importados: string[]; ignorados: { arquivo: string; motivo: string }[] }> {
  const form = new FormData()
  arquivos.forEach((f) => form.append('arquivos', f))
  return request('/importar/arquivo', { method: 'POST', body: form })
}

export async function importarTexto(texto: string): Promise<{ ok: boolean }> {
  return request('/importar/texto', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ texto }),
  })
}

export async function getHistorico(): Promise<HistoricoListResponse> {
  return request<HistoricoListResponse>('/historico')
}

export async function getFicha(id: string): Promise<HistoricoDetalhe> {
  return request<HistoricoDetalhe>(`/historico/${id}`)
}

export async function getStats(): Promise<StatsResponse> {
  return request<StatsResponse>('/stats')
}

export async function reclassificar(): Promise<{ atualizados: number; total: number }> {
  return request('/api/reclassificar', { method: 'POST' })
}

export async function getLogs(limit = 100): Promise<{ log: string[]; errors: string[] }> {
  return request(`/api/logs/recent?limit=${limit}`)
}

export function urlArquivo(analiseId: string, arquivoId: string): string {
  return `${BASE}/historico/${analiseId}/arquivos/${arquivoId}`
}

export function pingHealth(): void {
  if (!BASE) return
  fetch(`${BASE}/health`).catch(() => {})
}
