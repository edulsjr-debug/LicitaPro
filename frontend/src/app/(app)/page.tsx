'use client'

import Link from 'next/link'
import { useEffect, useMemo, useState } from 'react'
import clsx from 'clsx'
import { getHistorico, getStats } from '@/lib/api'
import type { HistoricoItem, StatsResponse } from '@/lib/types'
import { dataRelativa, estimarMinutos, formatarMoedaBRL, parseValorBRL } from '@/lib/utils'
import { ScoreBadge } from '@/components/ScoreBadge'
import { SegmentoBadge } from '@/components/SegmentoBadge'
import { Skeleton } from '@/components/Skeleton'

function scoreColor(score: number) {
  if (score >= 70) return 'bg-green-500'
  if (score >= 40) return 'bg-yellow-500'
  return 'bg-red-500'
}

function StatCard({ label, value, sub, children }: { label: string; value: React.ReactNode; sub?: string; children?: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <p className="text-sm font-medium text-gray-500">{label}</p>
      <div className="mt-2 text-3xl font-semibold tracking-normal text-gray-950">{value}</div>
      {sub ? <p className="mt-1 text-xs text-gray-500">{sub}</p> : null}
      {children}
    </div>
  )
}

export default function HomePage() {
  const [stats, setStats] = useState<StatsResponse | null>(null)
  const [historico, setHistorico] = useState<HistoricoItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const [statsResponse, historicoResponse] = await Promise.all([getStats(), getHistorico()])
      setStats(statsResponse)
      setHistorico(historicoResponse.historico)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Nao foi possivel carregar o dashboard.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const latest = useMemo(
    () =>
      [...historico]
        .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
        .slice(0, 10),
    [historico]
  )

  const scoreMedio = useMemo(() => {
    if (typeof stats?.score_medio === 'number') return stats.score_medio
    if (!historico.length) return 0
    return Math.round(historico.reduce((sum, item) => sum + (item.score || 0), 0) / historico.length)
  }, [historico, stats?.score_medio])

  const totalSalvo = stats?.historico_n ?? historico.length
  const limiteDiario = stats?.limite_diario ?? 20
  const altaViabilidade = stats?.score_distribuicao?.alta ?? historico.filter((item) => (item.score || 0) >= 75).length
  const mediaViabilidade = stats?.score_distribuicao?.media ?? historico.filter((item) => { const s = item.score || 0; return s >= 40 && s < 75 }).length
  const baixaViabilidade = stats?.score_distribuicao?.baixa ?? historico.filter((item) => (item.score || 0) < 40 && (item.score || 0) > 0).length
  const custoTotal = stats?.custo_usd_total ?? 0

  const minutosSalvos = useMemo(
    () => historico.reduce((sum, item) => sum + estimarMinutos(item.tamanho_total_bytes || 0), 0),
    [historico]
  )
  const tempoEconomizado = minutosSalvos >= 60
    ? `${Math.floor(minutosSalvos / 60)}h${minutosSalvos % 60 > 0 ? ` ${minutosSalvos % 60}min` : ''}`
    : `${minutosSalvos} min`

  const custoPorAnalise = totalSalvo > 0 && custoTotal > 0
    ? `$${(custoTotal / totalSalvo).toFixed(4)}`
    : null

  const taxaAproveitamento = totalSalvo > 0 ? Math.round((altaViabilidade / totalSalvo) * 100) : 0

  const valorTotalAvaliado = useMemo(
    () => historico.reduce((sum, item) => sum + parseValorBRL(item.valor), 0),
    [historico]
  )

  const valorAltaViabilidade = useMemo(
    () => historico.filter((item) => (item.score || 0) >= 75).reduce((sum, item) => sum + parseValorBRL(item.valor), 0),
    [historico]
  )

  const topOportunidades = useMemo(
    () =>
      [...historico]
        .filter((item) => (item.score || 0) > 0)
        .sort((a, b) => (b.score || 0) - (a.score || 0))
        .slice(0, 3),
    [historico]
  )

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal text-gray-950">Dashboard</h1>
          <p className="mt-1 text-sm text-gray-600">Resumo de produtividade e pipeline de editais.</p>
        </div>
        <Link href="/novo" className="rounded-md bg-brand-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-brand-700">
          Novo edital
        </Link>
      </div>

      {loading ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-32" />)}
          </div>
          <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-32" />)}
          </div>
          <Skeleton className="mt-8 h-48" />
          <Skeleton className="mt-8 h-96" />
        </>
      ) : error ? (
        <section className="rounded-lg border border-red-200 bg-red-50 p-5 text-sm text-red-700">
          <p>{error}</p>
          <button type="button" onClick={load} className="mt-3 rounded-md bg-red-100 px-3 py-2 font-semibold text-red-800">
            Tentar novamente
          </button>
        </section>
      ) : (
        <>
          {/* Linha 1 — Produtividade */}
          <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              label="Análises hoje"
              value={
                <>
                  {stats?.analises_hoje ?? 0}
                  <span className="ml-1 text-base font-medium text-gray-400">/ {limiteDiario}</span>
                </>
              }
              sub="Limite diário — reseta à meia-noite"
            >
              <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-gray-100">
                <div className="h-full rounded-full bg-brand-500 transition-all" style={{ width: `${Math.min(100, ((stats?.analises_hoje ?? 0) / limiteDiario) * 100)}%` }} />
              </div>
            </StatCard>

            <StatCard
              label="Tempo economizado"
              value={totalSalvo > 0 ? tempoEconomizado : '—'}
              sub={totalSalvo > 0 ? `Estimado pelo tamanho real dos arquivos` : 'Nenhum edital analisado ainda'}
            />

            <StatCard
              label="Custo por análise"
              value={custoPorAnalise ?? '—'}
              sub={custoPorAnalise ? `Total acumulado: $${custoTotal.toFixed(4)}` : 'Nenhum uso de IA ainda'}
            />

            <StatCard
              label="Taxa de aproveitamento"
              value={totalSalvo > 0 ? `${taxaAproveitamento}%` : '—'}
              sub={totalSalvo > 0 ? `${altaViabilidade} de alta viabilidade (≥ 75 pts)` : 'Sem dados'}
            >
              {totalSalvo > 0 ? (
                <div className="mt-3 flex h-2 overflow-hidden rounded-full">
                  <div className="bg-green-500 transition-all" style={{ width: `${(altaViabilidade / totalSalvo) * 100}%` }} title={`Alta: ${altaViabilidade}`} />
                  <div className="bg-yellow-400 transition-all" style={{ width: `${(mediaViabilidade / totalSalvo) * 100}%` }} title={`Média: ${mediaViabilidade}`} />
                  <div className="flex-1 bg-red-400" title={`Baixa: ${baixaViabilidade}`} />
                </div>
              ) : null}
            </StatCard>
          </section>

          {/* Linha 2 — Pipeline financeiro */}
          <section className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <StatCard
              label="Valor total avaliado"
              value={valorTotalAvaliado > 0 ? formatarMoedaBRL(valorTotalAvaliado) : '—'}
              sub={valorTotalAvaliado > 0 ? 'Soma dos contratos analisados' : 'Nenhum valor identificado ainda'}
            />

            <StatCard
              label="Oportunidades qualificadas"
              value={valorAltaViabilidade > 0 ? formatarMoedaBRL(valorAltaViabilidade) : '—'}
              sub={valorAltaViabilidade > 0 ? `Contratos com score ≥ 75` : `${altaViabilidade} editais de alta viabilidade`}
            />

            <StatCard label="Score médio" value={scoreMedio || '—'}>
              <div className="mt-3 h-2 overflow-hidden rounded-full bg-gray-100">
                <div className={clsx('h-full rounded-full transition-all', scoreColor(scoreMedio))} style={{ width: `${Math.min(100, scoreMedio)}%` }} />
              </div>
              {totalSalvo > 0 ? (
                <div className="mt-2 flex gap-3 text-xs text-gray-500">
                  <span className="text-green-600">{altaViabilidade} alta</span>
                  <span className="text-yellow-600">{mediaViabilidade} média</span>
                  <span className="text-red-500">{baixaViabilidade} baixa</span>
                </div>
              ) : null}
            </StatCard>
          </section>

          {/* Top oportunidades */}
          {topOportunidades.length > 0 ? (
            <section className="mt-8">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-950">Top oportunidades</h2>
                <span className="text-xs text-gray-400">Maiores scores do histórico</span>
              </div>
              <div className="grid gap-3 sm:grid-cols-3">
                {topOportunidades.map((item, idx) => (
                  <Link
                    key={item.id}
                    href={`/historico/${item.id}`}
                    className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition hover:border-brand-200 hover:shadow-md"
                  >
                    <div className="mb-2 flex items-start justify-between gap-2">
                      <span className="text-xs font-bold text-gray-300">#{idx + 1}</span>
                      <ScoreBadge score={item.score || 0} />
                    </div>
                    <h3 className="truncate text-sm font-semibold text-gray-950">{item.nome || item.orgao || 'Sem identificação'}</h3>
                    <p className="mt-1 line-clamp-2 text-xs leading-5 text-gray-500">{item.objeto || 'Objeto não informado'}</p>
                    <div className="mt-2">
                      <SegmentoBadge segmento={item.segmento} />
                    </div>
                  </Link>
                ))}
              </div>
            </section>
          ) : null}

          {/* Últimas análises */}
          <section className="mt-8">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-950">Últimas análises</h2>
              <Link href="/historico" className="text-sm font-medium text-brand-700 hover:text-brand-800">
                Ver todos
              </Link>
            </div>

            {latest.length ? (
              <div className="grid gap-3">
                {latest.map((item) => (
                  <Link
                    key={item.id}
                    href={`/historico/${item.id}`}
                    className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition hover:border-brand-200 hover:shadow-md"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="min-w-0">
                        <h3 className="truncate text-sm font-semibold text-gray-950">{item.nome || item.orgao || 'Sem identificação'}</h3>
                        <p className="mt-1 line-clamp-2 text-sm leading-6 text-gray-600">{item.objeto || 'Objeto nao informado'}</p>
                      </div>
                      <ScoreBadge score={item.score || 0} />
                    </div>
                    <div className="mt-3 flex flex-wrap items-center gap-2 text-sm text-gray-500">
                      <SegmentoBadge segmento={item.segmento} />
                      <span>{dataRelativa(item.timestamp)}</span>
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="rounded-lg border border-gray-200 bg-white p-8 text-center shadow-sm">
                <p className="text-sm text-gray-600">Nenhuma analise ainda.</p>
                <Link href="/novo" className="mt-3 inline-flex rounded-md bg-brand-600 px-3 py-2 text-sm font-semibold text-white">
                  Analisar primeiro edital
                </Link>
              </div>
            )}
          </section>
        </>
      )}
    </div>
  )
}
