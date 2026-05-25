'use client'

import Link from 'next/link'
import { useParams } from 'next/navigation'
import { useEffect, useState } from 'react'
import { getFicha, getHistorico, urlArquivo } from '@/lib/api'
import type { HistoricoDetalhe } from '@/lib/types'
import { extrairJustificativas, formatarBytes, formatarData } from '@/lib/utils'
import { FichaMarkdown } from '@/components/FichaMarkdown'
import { ScoreBadge } from '@/components/ScoreBadge'
import { SegmentoBadge } from '@/components/SegmentoBadge'
import { Skeleton } from '@/components/Skeleton'

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
        const [response, historico] = await Promise.all([getFicha(params.id), getHistorico().catch(() => ({ historico: [] }))])
        const resumo = historico.historico.find((registro) => registro.id === params.id)
        if (mounted) {
          setItem({
            ...resumo,
            ...response,
            id: params.id,
            timestamp: response.timestamp || resumo?.timestamp || '',
            objeto: response.objeto || resumo?.objeto || '',
            valor: response.valor || resumo?.valor || '',
          })
        }
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
    <div>
      <div className="mb-5 flex items-center gap-2 text-sm text-gray-500">
        <Link href="/historico" className="font-medium text-brand-700 hover:text-brand-800">
          Historico
        </Link>
        <span>/</span>
        <span className="truncate">{item?.orgao || 'Analise'}</span>
      </div>

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
              <SegmentoBadge segmento={item.segmento} showTooltip />
              <ScoreBadge score={item.score || 0} breakdown={extrairJustificativas(item.ficha || '')} />
              {item.timestamp ? <span className="text-sm text-gray-500">{formatarData(item.timestamp)}</span> : null}
            </div>
            <h1 className="text-2xl font-semibold tracking-normal text-gray-950">{item.nome || item.orgao || 'Sem identificação'}</h1>
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

          {item.arquivos?.length ? (
            <section className="mb-5 rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
              <h2 className="text-sm font-semibold text-gray-950">Arquivos anexados</h2>
              <div className="mt-3 space-y-2">
                {[...item.arquivos].sort((a, b) => (a.ordem || 0) - (b.ordem || 0)).map((arquivo) => {
                  const nome = arquivo.arquivo || arquivo.nome_original || 'arquivo'
                  return (
                    <div key={arquivo.id} className="flex items-center justify-between gap-3 rounded-md border border-gray-100 px-3 py-2">
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium text-gray-900">{nome}</p>
                        <p className="text-xs text-gray-500">
                          {arquivo.mime_type || 'application/octet-stream'}
                          {arquivo.tamanho_bytes ? ` - ${formatarBytes(arquivo.tamanho_bytes)}` : ''}
                        </p>
                      </div>
                      <a
                        href={urlArquivo(params.id, arquivo.id)}
                        className="rounded-md border border-gray-200 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
                      >
                        Baixar
                      </a>
                    </div>
                  )
                })}
              </div>
            </section>
          ) : null}

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
    </div>
  )
}
