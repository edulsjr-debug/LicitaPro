'use client'

import Link from 'next/link'
import { useEffect, useMemo, useState } from 'react'
import { getHistorico } from '@/lib/api'
import type { HistoricoItem } from '@/lib/types'
import { diaGrupo, horaCurta } from '@/lib/utils'
import { ScoreBadge } from '@/components/ScoreBadge'
import { SegmentoBadge } from '@/components/SegmentoBadge'
import { Skeleton } from '@/components/Skeleton'

const scoreOptions = [
  { value: 'todos', label: 'Todos' },
  { value: 'alto', label: '>=70 Alta' },
  { value: 'medio', label: '40-69 Media' },
  { value: 'baixo', label: '<40 Baixa' },
]

function matchesScore(score: number, filter: string) {
  if (filter === 'alto') return score >= 70
  if (filter === 'medio') return score >= 40 && score < 70
  if (filter === 'baixo') return score < 40
  return true
}

export default function HistoricoPage() {
  const [items, setItems] = useState<HistoricoItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState('')
  const [segmento, setSegmento] = useState('Todos')
  const [score, setScore] = useState('todos')

  async function load() {
    setLoading(true)
    setError(null)

    try {
      const response = await getHistorico()
      setItems(response.historico)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Nao foi possivel carregar o historico.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const segmentos = useMemo(() => ['Todos', ...Array.from(new Set(items.map((item) => item.segmento).filter(Boolean)))], [items])

  const filtered = useMemo(() => {
    const term = query.trim().toLowerCase()

    return [...items]
      .filter((item) => {
        const text = `${item.orgao} ${item.objeto}`.toLowerCase()
        return (
          (!term || text.includes(term)) &&
          (segmento === 'Todos' || item.segmento === segmento) &&
          matchesScore(item.score || 0, score)
        )
      })
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
  }, [items, query, segmento, score])

  const groups = useMemo(() => {
    return filtered.reduce<Record<string, HistoricoItem[]>>((acc, item) => {
      const label = diaGrupo(item.timestamp)
      acc[label] = acc[label] || []
      acc[label].push(item)
      return acc
    }, {})
  }, [filtered])

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal text-gray-950">Historico</h1>
          <p className="mt-1 text-sm text-gray-600">Todas as analises agrupadas por dia.</p>
        </div>
        <Link href="/novo" className="rounded-md bg-brand-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-brand-700">
          Novo edital
        </Link>
      </div>

      <section className="mb-5 grid gap-3 rounded-lg border border-gray-200 bg-white p-4 shadow-sm md:grid-cols-[1fr_220px_160px]">
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Buscar por orgao ou objeto"
          className="h-10 rounded-md border border-gray-200 px-3 text-sm outline-none ring-brand-100 focus:border-brand-500 focus:ring-2"
        />
        <select
          value={segmento}
          onChange={(event) => setSegmento(event.target.value)}
          className="h-10 rounded-md border border-gray-200 px-3 text-sm outline-none ring-brand-100 focus:border-brand-500 focus:ring-2"
        >
          {segmentos.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
        <select
          value={score}
          onChange={(event) => setScore(event.target.value)}
          className="h-10 rounded-md border border-gray-200 px-3 text-sm outline-none ring-brand-100 focus:border-brand-500 focus:ring-2"
        >
          {scoreOptions.map((item) => (
            <option key={item.value} value={item.value}>
              {item.label}
            </option>
          ))}
        </select>
      </section>

      {loading ? (
        <div className="grid gap-3">
          {Array.from({ length: 4 }).map((_, index) => (
            <Skeleton key={index} className="h-32" />
          ))}
        </div>
      ) : error ? (
        <div className="rounded-lg border border-red-200 bg-red-50 p-5 text-sm text-red-700">
          <p>{error}</p>
          <button type="button" onClick={load} className="mt-3 rounded-md bg-red-100 px-3 py-2 font-semibold text-red-800">
            Tentar novamente
          </button>
        </div>
      ) : !items.length ? (
        <div className="rounded-lg border border-gray-200 bg-white p-8 text-center shadow-sm">
          <p className="text-sm font-medium text-gray-700">Nenhuma analise ainda</p>
          <Link href="/novo" className="mt-3 inline-flex rounded-md bg-brand-600 px-3 py-2 text-sm font-semibold text-white">
            Criar primeira analise
          </Link>
        </div>
      ) : filtered.length ? (
        <div className="space-y-8">
          {Object.entries(groups).map(([day, dayItems]) => (
            <section key={day}>
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-500">{day}</h2>
              <div className="grid gap-3">
                {dayItems.map((item) => (
                  <Link
                    key={item.id}
                    href={`/historico/${item.id}`}
                    className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition hover:border-brand-200 hover:shadow-md"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="min-w-0">
                        <h3 className="truncate text-base font-semibold text-gray-950">{item.orgao || 'Orgao nao informado'}</h3>
                        <p className="mt-1 line-clamp-2 text-sm leading-6 text-gray-600">{item.objeto || 'Objeto nao informado'}</p>
                      </div>
                      <ScoreBadge score={item.score || 0} />
                    </div>
                    <div className="mt-4 flex flex-wrap items-center gap-2 text-sm text-gray-500">
                      <SegmentoBadge segmento={item.segmento} />
                      <span>{horaCurta(item.timestamp)}</span>
                    </div>
                  </Link>
                ))}
              </div>
            </section>
          ))}
        </div>
      ) : (
        <div className="rounded-lg border border-gray-200 bg-white p-6 text-center text-sm text-gray-600 shadow-sm">
          Nenhuma analise encontrada com estes filtros.
        </div>
      )}
    </div>
  )
}
