'use client'

import Link from 'next/link'
import { useEffect, useMemo, useState } from 'react'
import clsx from 'clsx'
import { getHistorico, getStats } from '@/lib/api'
import type { HistoricoItem, StatsResponse } from '@/lib/types'
import { dataRelativa } from '@/lib/utils'
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
  const tokensTotal = (stats?.tokens_input_total ?? 0) + (stats?.tokens_output_total ?? 0)
  const segmentosTop = stats?.segmentos_top ?? {}
  const topSegmento = Object.entries(segmentosTop).sort((a, b) => b[1] - a[1])[0]

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal text-gray-950">Editais analisados</h1>
          <p className="mt-1 text-sm text-gray-600">Resumo dos editais salvos e ordenados por data.</p>
        </div>
        <Link href="/novo" className="rounded-md bg-brand-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-brand-700">
          Novo edital
        </Link>
      </div>

      {loading ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {Array.from({ length: 4 }).map((_, index) => (
              <Skeleton key={index} className="h-32" />
            ))}
          </div>
          <Skeleton className="mt-6 h-96" />
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
          <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
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

            <StatCard label="Total no histórico" value={totalSalvo} sub={`${altaViabilidade} de alta viabilidade (≥ 75)`}>
              {totalSalvo > 0 ? (
                <div className="mt-3 flex h-2 overflow-hidden rounded-full">
                  <div className="bg-green-500 transition-all" style={{ width: `${(altaViabilidade / totalSalvo) * 100}%` }} title={`Alta: ${altaViabilidade}`} />
                  <div className="bg-yellow-400 transition-all" style={{ width: `${(mediaViabilidade / totalSalvo) * 100}%` }} title={`Média: ${mediaViabilidade}`} />
                  <div className="flex-1 bg-red-400" title={`Baixa: ${baixaViabilidade}`} />
                </div>
              ) : null}
            </StatCard>

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

            <StatCard
              label="Custo IA acumulado"
              value={custoTotal > 0 ? `$${custoTotal.toFixed(4)}` : '$0'}
              sub={tokensTotal > 0 ? `${(tokensTotal / 1000).toFixed(1)}k tokens consumidos` : 'Nenhum token consumido ainda'}
            />

            <StatCard
              label="Segmento mais analisado"
              value={topSegmento ? topSegmento[0] : '—'}
              sub={topSegmento ? `${topSegmento[1]} edital${topSegmento[1] > 1 ? 'is' : ''}` : 'Sem dados'}
            />

            <StatCard
              label="Provedores de IA"
              value={Object.keys(stats?.por_provedor ?? {}).length || '—'}
              sub={Object.entries(stats?.por_provedor ?? {}).sort((a, b) => b[1].analises - a[1].analises)[0]?.[0] ?? 'Nenhum uso ainda'}
            />
          </section>

          <section className="mt-8">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-950">Recentes</h2>
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
