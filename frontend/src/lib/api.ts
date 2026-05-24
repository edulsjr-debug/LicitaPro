import type {
  AnalisarResponse,
  HistoricoDetalhe,
  HistoricoListResponse,
  Modo,
  StatsResponse,
} from './types'

const BASE = process.env.NEXT_PUBLIC_API_URL ?? ''

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  if (!BASE) throw new Error('NEXT_PUBLIC_API_URL não configurada — verifique as variáveis de ambiente da Vercel.')
  const res = await fetch(`${BASE}${path}`, init)
  if (!res.ok) {
    const err = await res.text().catch(() => res.statusText)
    throw new Error(err || `HTTP ${res.status}`)
  }
  return res.json() as Promise<T>
}

export async function analisarArquivos(
  arquivos: File[],
  modo: Modo = 'auto'
): Promise<AnalisarResponse> {
  if (!BASE) throw new Error('NEXT_PUBLIC_API_URL não configurada — verifique as variáveis de ambiente da Vercel.')
  const form = new FormData()
  arquivos.forEach((f) => form.append('arquivos', f))
  form.append('modo', modo)

  // POST retorna job_id imediatamente — sem timeout possível
  const res = await fetch(`${BASE}/analisar/arquivo`, { method: 'POST', body: form })
  if (!res.ok) {
    const err = await res.text().catch(() => res.statusText)
    throw new Error(err || `HTTP ${res.status}`)
  }
  const { job_id } = await res.json() as { job_id: string }

  // Polling a cada 3s até o job terminar (até 10 minutos)
  const MAX_MS = 10 * 60 * 1000
  const start = Date.now()
  while (Date.now() - start < MAX_MS) {
    await new Promise((r) => setTimeout(r, 3000))
    const poll = await fetch(`${BASE}/analisar/job/${job_id}`)
    if (!poll.ok) continue
    const job = await poll.json() as { status: string; error?: string } & AnalisarResponse
    if (job.status === 'done') return job
    if (job.status === 'error') throw new Error(job.error ?? 'Erro na análise.')
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
