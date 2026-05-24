export function extrairScore(ficha: string): number {
  const match = ficha.match(/Score[^:]*:\*?\*?\s*(\d+)\/100/) || ficha.match(/\*\*Score:\*\*\s*(\d+)/)
  return match ? Math.min(100, Math.max(0, Number.parseInt(match[1], 10))) : 0
}

export function extrairSegmento(ficha: string): string {
  const match = ficha.match(/Segmento[^:]*:\*?\*?\s*([^\n]+)/i) || ficha.match(/\*\*Segmento:\*\*\s*([^\n]+)/i)
  return match ? match[1].replace(/\*/g, '').trim() : 'Outros'
}

export function formatarData(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return iso

  return new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

export function dataRelativa(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return iso

  const minutes = Math.max(0, Math.round((Date.now() - date.getTime()) / 60000))
  if (minutes < 1) return 'agora'
  if (minutes < 60) return `ha ${minutes} min`

  const hours = Math.round(minutes / 60)
  if (hours < 24) return `ha ${hours} hora${hours === 1 ? '' : 's'}`

  const days = Math.round(hours / 24)
  return `ha ${days} dia${days === 1 ? '' : 's'}`
}

export function formatarBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1).replace('.', ',')} KB`
  return `${(bytes / 1024 / 1024).toFixed(1).replace('.', ',')} MB`
}

export function horaCurta(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return ''
  return new Intl.DateTimeFormat('pt-BR', { hour: '2-digit', minute: '2-digit' }).format(date)
}

export function diaGrupo(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return iso || 'Sem data'

  const today = new Date()
  const yesterday = new Date()
  yesterday.setDate(today.getDate() - 1)

  const key = date.toISOString().slice(0, 10)
  if (key === today.toISOString().slice(0, 10)) return 'Hoje'
  if (key === yesterday.toISOString().slice(0, 10)) return 'Ontem'

  return new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  }).format(date)
}
