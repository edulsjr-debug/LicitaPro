export interface HistoricoItem {
  id: string
  timestamp: string
  orgao: string
  valor: string
  objeto: string
  segmento: string
  score: number
  arquivos?: HistoricoArquivo[]
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
  historico_n?: number
  limite_diario?: number
  analises_hoje: number
  por_provedor: Record<string, { analises: number; tokens_in: number; tokens_out: number; custo: number }>
  versao: string
  commit: string
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
