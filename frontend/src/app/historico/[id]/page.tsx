'use client'

import Link from 'next/link'
import { useParams } from 'next/navigation'
import { useEffect, useState } from 'react'
import { getFicha } from '@/lib/api'
import type { HistoricoDetalhe } from '@/lib/types'
import { FichaMarkdown } from '@/components/FichaMarkdown'
import { ScoreBadge } from '@/components/ScoreBadge'
import { SegmentoBadge } from '@/components/SegmentoBadge'
import { Skeleton } from '@/components/Skeleton'

function formatDate(value: string) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value

  return new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

export default function FichaPage() {
  const params = useParams<{ id: string }>()
  const [item, setItem] = useState<HistoricoDetalhe | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    let mounted = true

    async function load() {
      setLoading(true)
      setError(null)

      try {
        const response = await getFicha(params.id)
        if (mounted) setItem(response)
      } catch (err) {
        if (mounted) setError(err instanceof Error ? err.message : 'Analise nao encontrada')
      } finally {
        if (mounted) setLoading(false)
      }
    }

    load()

    return () => {
      mounted = false
    }
  }, [params.id])

  async function copiarFicha() {
    if (!item?.ficha) return
    await navigator.clipboard.writeText(item.ficha)
    setCopied(true)
    window.setTimeout(() => setCopied(false), 1800)
  }

  return (
    <main className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
      <Link href="/historico" className="mb-5 inline-flex text-sm font-medium text-gray-600 hover:text-gray-950">
        Voltar ao historico
      </Link>

      {loading ? (
        <div className="space-y-4">
          <Skeleton className="h-12 w-2/3" />
          <Skeleton className="h-24" />
          <Skeleton className="h-96" />
        </div>
      ) : error || !item ? (
        <section className="rounded-lg border border-gray-200 bg-white p-8 text-center shadow-sm">
          <h1 className="text-lg font-semibold text-gray-950">Analise nao encontrada</h1>
          <p className="mt-2 text-sm text-gray-600">{error}</p>
        </section>
      ) : (
        <>
          <header className="mb-5">
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <SegmentoBadge segmento={item.segmento} />
              <ScoreBadge score={item.score} />
              <span className="text-sm text-gray-500">{formatDate(item.timestamp)}</span>
            </div>
            <h1 className="text-2xl font-semibold tracking-normal text-gray-950">{item.orgao || 'Orgao nao informado'}</h1>
          </header>

          <section className="mb-5 rounded-lg border border-gray-200 bg-gray-50 p-4">
            <p className="text-sm font-medium text-gray-500">Objeto</p>
            <p className="mt-1 text-sm leading-6 text-gray-800">{item.objeto || 'Objeto nao informado'}</p>
            {item.valor ? (
              <p className="mt-3 text-sm text-gray-700">
                <span className="font-medium">Valor estimado:</span> {item.valor}
              </p>
            ) : null}
          </section>

          <div className="mb-4 flex justify-end">
            <button
              type="button"
              onClick={copiarFicha}
              className="rounded-md bg-brand-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-brand-700"
            >
              {copied ? 'Copiado' : 'Copiar ficha'}
            </button>
          </div>

          <section className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
            <FichaMarkdown ficha={item.ficha} />
          </section>
        </>
      )}
    </main>
  )
}
