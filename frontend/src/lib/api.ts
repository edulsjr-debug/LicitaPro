import type {
  AnalisarResponse,
  HistoricoDetalhe,
  HistoricoListResponse,
  Modo,
  StatsResponse,
} from './types'

const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
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
  const form = new FormData()
  arquivos.forEach((f) => form.append('arquivos', f))
  form.append('modo', modo)
  return request<AnalisarResponse>('/analisar/arquivo', { method: 'POST', body: form })
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
