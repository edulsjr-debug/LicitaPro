export function extrairScore(ficha: string): number {
  // formato parser: **65/100 — Média**
  // formato IA: **Score:** 65  ou  Score de Viabilidade: **65**/100
  const match =
    ficha.match(/\*\*(\d+)\/100/) ||
    ficha.match(/Score[^:]*:\*?\*?\s*(\d+)\/100/) ||
    ficha.match(/\*\*Score:\*\*\s*(\d+)/)
  return match ? Math.min(100, Math.max(0, Number.parseInt(match[1], 10))) : 0
}

export function extrairSegmento(ficha: string): string {
  // formato parser (justificativa): "Segmento Viagens e Passagens: 20/40 pts"
  const parserMatch = ficha.match(/Segmento\s+([^:\n]+?):\s*\d+\/\d+/i)
  if (parserMatch) return parserMatch[1].trim()
  // formato IA: **Segmento:** Viagens
  const iaMatch = ficha.match(/\*\*Segmento:\*\*\s*([^\n|]+)/i) || ficha.match(/Segmento:\s*([^\n|]+)/i)
  return iaMatch ? iaMatch[1].replace(/\*/g, '').trim() : 'Outros'
}

const TZ = 'America/Sao_Paulo'

export function formatarData(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return iso

  return new Intl.DateTimeFormat('pt-BR', {
    timeZone: TZ,
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

export function formatarDuracao(segundos: number): string {
  if (segundos < 60) return `${Math.round(segundos)}s`
  const minutos = Math.floor(segundos / 60)
  const resto = Math.round(segundos % 60)
  return `${minutos}m ${resto}s`
}

export function formatarBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1).replace('.', ',')} KB`
  return `${(bytes / 1024 / 1024).toFixed(1).replace('.', ',')} MB`
}

export function extrairJustificativas(ficha: string): string[] {
  const section = ficha.match(/##\s*Score de Viabilidade([\s\S]*?)(?=\n##|$)/i)?.[1] ?? ''
  return [...section.matchAll(/^[-•*]\s*(.+)$/gm)]
    .map((m) => m[1].trim())
    .filter(Boolean)
}

function dateSP(iso: string): string {
  return new Intl.DateTimeFormat('pt-BR', {
    timeZone: TZ,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  })
    .format(new Date(iso))
    .split('/')
    .reverse()
    .join('-')
}

export function horaCurta(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return ''
  return new Intl.DateTimeFormat('pt-BR', { timeZone: TZ, hour: '2-digit', minute: '2-digit' }).format(date)
}

/**
 * Estima minutos de leitura+análise humana a partir do tamanho total dos arquivos.
 * Calibração: ~1 min por 15KB (documentos técnicos complexos).
 * Mínimo 15 min (qualquer edital exige atenção), máximo 180 min.
 * Para análises de texto sem arquivo (bytes=0): retorna 20 min como base.
 */
export function estimarMinutos(bytes: number): number {
  if (!bytes) return 20
  return Math.min(180, Math.max(15, Math.round(bytes / 15_000)))
}

/** "R$ 2.000.000,00" → 2000000  |  retorna 0 se não parsear */
export function parseValorBRL(valor: string | undefined): number {
  if (!valor) return 0
  const m = valor.match(/([\d.,]+)/)
  if (!m) return 0
  const n = parseFloat(m[1].replace(/\./g, '').replace(',', '.'))
  return Number.isFinite(n) ? n : 0
}

/** 2000000 → "R$ 2,0 mi"  |  9500000000 → "R$ 9,5 bi" */
export function formatarMoedaBRL(valor: number): string {
  if (valor === 0) return 'R$ 0'
  if (valor >= 1_000_000_000) return `R$ ${(valor / 1_000_000_000).toFixed(1).replace('.', ',')} bi`
  if (valor >= 1_000_000) return `R$ ${(valor / 1_000_000).toFixed(1).replace('.', ',')} mi`
  if (valor >= 1_000) return `R$ ${(valor / 1_000).toFixed(0)} mil`
  return `R$ ${valor.toFixed(0)}`
}

export function diaGrupo(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return iso || 'Sem data'

  const key = dateSP(iso)
  if (key === dateSP(new Date().toISOString())) return 'Hoje'
  if (key === dateSP(new Date(Date.now() - 86_400_000).toISOString())) return 'Ontem'

  return new Intl.DateTimeFormat('pt-BR', {
    timeZone: TZ,
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  }).format(date)
}
