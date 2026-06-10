export interface HistoricoItem {
  id: string
  timestamp: string
  nome?: string
  orgao: string
  valor: string
  objeto: string
  segmento: string
  score: number
  arquivos?: HistoricoArquivo[]
  tamanho_total_bytes?: number
  tempo_decorrido_segundos?: number | null
}

export interface HistoricoDetalhe extends HistoricoItem {
  ficha: string
  fonte?: string
}

export interface HistoricoArquivo {
  id: string
  arquivo?: string
  nome_original?: string
  mime_type?: string
  tamanho_bytes?: number
  ordem?: number
}

export interface AnalisarResponse {
  ficha: string
  id?: string
  persistido?: boolean
  aviso?: string
  tempo_decorrido_segundos?: number | null
}

export interface JobStatus {
  status: string
  error?: string
  progresso?: string
  eta_segundos?: number
}

export interface HistoricoListResponse {
  historico: HistoricoItem[]
}

export interface StatsResponse {
  total_analises: number
  tokens_input_total: number
  tokens_output_total: number
  custo_usd_total: number
  score_medio?: number
  score_distribuicao?: { alta: number; media: number; baixa: number }
  segmentos_top?: Record<string, number>
  segmentos_lista?: string[]
  historico_n?: number
  limite_diario?: number
  analises_hoje: number
  limite_diario_atingido?: boolean
  ia_disponivel?: boolean
  ia_quota_reset?: string
  por_provedor: Record<string, { analises: number; tokens: number; custo_usd: number }>
  versao: string
  commit: string
  db_ok?: boolean
}

export type Modo = 'auto' | 'parser' | 'ia'

export type Segmento =
  | 'Saúde'
  | 'Educação'
  | 'Obras e Infraestrutura'
  | 'Alimentação'
  | 'Tecnologia e TI'
  | 'Transporte'
  | 'Viagens e Passagens'
  | 'Eventos e Capacitação'
  | 'Limpeza e Conservação'
  | 'Mobiliário e Escritório'
  | 'Segurança'
  | 'Outros'
