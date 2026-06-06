'use client'

export interface ClientError {
  ts: string
  url: string
  method: string
  status?: number
  message: string
}

const KEY = 'licitapro_client_errors'
const MAX = 100

export function recordError(url: string, method: string, error: unknown, status?: number) {
  if (typeof window === 'undefined') return
  try {
    const list: ClientError[] = JSON.parse(localStorage.getItem(KEY) ?? '[]')
    list.push({
      ts: new Date().toISOString(),
      url,
      method: method.toUpperCase(),
      status,
      message: error instanceof Error ? error.message : String(error),
    })
    if (list.length > MAX) list.splice(0, list.length - MAX)
    localStorage.setItem(KEY, JSON.stringify(list))
  } catch {}
}

export function getClientErrors(): ClientError[] {
  if (typeof window === 'undefined') return []
  try {
    return JSON.parse(localStorage.getItem(KEY) ?? '[]')
  } catch {
    return []
  }
}

export function clearClientErrors() {
  if (typeof window === 'undefined') return
  localStorage.removeItem(KEY)
}
