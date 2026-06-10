'use client'

import Link from 'next/link'
import { useParams } from 'next/navigation'
import { useEffect, useRef, useState } from 'react'
import { atualizarSegmento, getFicha, getHistorico, getStats, urlArquivo } from '@/lib/api'
import type { HistoricoDetalhe } from '@/lib/types'
import { extrairJustificativas, formatarBytes, formatarData, formatarDuracao } from '@/lib/utils'
import { FichaMarkdown } from '@/components/FichaMarkdown'
import { ScoreBadge } from '@/components/ScoreBadge'
import { SegmentoBadge } from '@/components/SegmentoBadge'
import { Skeleton } from '@/components/Skeleton'

const BASE = process.env.NEXT_PUBLIC_API_URL ?? ''

function NomeEditavel({ id, nome }: { id: string; nome: string }) {
  const [editando, setEditando] = useState(false)
  const [valor, setValor] = useState(nome)
  const [salvando, setSalvando] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => { setValor(nome) }, [nome])
  useEffect(() => { if (editando) inputRef.current?.select() }, [editando])

  async function salvar() {
    const novo = valor.trim()
    if (!novo || novo === nome) { setEditando(false); setValor(nome); return }
    setSalvando(true)
    try {
      await fetch(`${BASE}/historico/${id}/nome`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nome: novo }),
      })
      setEditando(false)
    } finally {
      setSalvando(false)
    }
  }

  if (editando) {
    return (
      <div className="flex items-center gap-2">
        <input
          ref={inputRef}
          value={valor}
          onChange={(e) => setValor(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') salvar(); if (e.key === 'Escape') { setEditando(false); setValor(nome) } }}
          onBlur={salvar}
          maxLength={120}
          disabled={salvando}
          className="w-full rounded-md border border-brand-300 px-2 py-1 text-2xl font-semibold tracking-normal text-gray-950 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
        />
      </div>
    )
  }

  return (
    <button
      type="button"
      onClick={() => setEditando(true)}
      title="Clique para renomear"
      className="group flex items-center gap-2 text-left"
    >
      <h1 className="text-2xl font-semibold tracking-normal text-gray-950">{valor || 'Sem identificação'}</h1>
      <svg viewBox="0 0 24 24" aria-hidden="true" className="h-4 w-4 flex-shrink-0 text-gray-300 opacity-0 transition group-hover:opacity-100">
        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </button>
  )
}

const SEGMENTOS_PADRAO = [
  'Saúde', 'Educação', 'Obras e Infraestrutura', 'Alimentação', 'Tecnologia e TI',
  'Transporte', 'Viagens e Passagens', 'Eventos e Capacitação', 'Limpeza e Conservação',
  'Mobiliário e Escritório', 'Segurança', 'Outros',
]

function SegmentoEditavel({ id, segmento, segmentos, onSave }: {
  id: string; segmento: string; segmentos: string[]; onSave: (seg: string) => void
}) {
  const [editando, setEditando] = useState(false)
  const [valor, setValor] = useState(segmento)
  const [novoCustom, setNovoCustom] = useState('')
  const [salvando, setSalvando] = useState(false)
  const selectRef = useRef<HTMLSelectElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => { setValor(segmento) }, [segmento])
  useEffect(() => { if (editando) selectRef.current?.focus() }, [editando])

  const lista = Array.from(new Set([...SEGMENTOS_PADRAO, ...segmentos])).sort((a, b) => a.localeCompare(b, 'pt-BR'))

  async function salvar(seg: string) {
    const novo = seg.trim()
    if (!novo || novo === segmento) { setEditando(false); setValor(segmento); return }
    setSalvando(true)
    try {
      await atualizarSegmento(id, novo)
      onSave(novo)
      setEditando(false)
    } finally {
      setSalvando(false)
    }
  }

  if (editando) {
    return (
      <div className="flex flex-wrap items-center gap-2">
        <select
          ref={selectRef}
          value={valor}
          onChange={(e) => { setValor(e.target.value); if (e.target.value !== '__novo__') salvar(e.target.value) }}
          onKeyDown={(e) => { if (e.key === 'Escape') { setEditando(false); setValor(segmento) } }}
          onBlur={() => { if (valor === '__novo__') return; setEditando(false); setValor(segmento) }}
          disabled={salvando}
          className="rounded-md border border-brand-300 px-2 py-1 text-sm font-medium text-gray-800 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
        >
          {lista.map((seg) => <option key={seg} value={seg}>{seg}</option>)}
          <option value="__novo__">Novo segmento…</option>
        </select>

        {valor === '__novo__' && (
          <input
            ref={inputRef}
            autoFocus
            value={novoCustom}
            onChange={(e) => setNovoCustom(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') salvar(novoCustom)
              if (e.key === 'Escape') { setEditando(false); setValor(segmento) }
            }}
            placeholder="Nome do segmento"
            maxLength={60}
            disabled={salvando}
            className="rounded-md border border-brand-300 px-2 py-1 text-sm text-gray-800 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
        )}
      </div>
    )
  }

  return (
    <button
      type="button"
      onClick={() => setEditando(true)}
      title="Clique para alterar segmento"
      className="rounded focus:outline-none focus:ring-2 focus:ring-brand-400"
    >
      <SegmentoBadge segmento={segmento} showTooltip tooltipDirection="below" />
    </button>
  )
}

export default function FichaPage() {
  const params = useParams<{ id: string }>()
  const [item, setItem] = useState<HistoricoDetalhe | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [segmentos, setSegmentos] = useState<string[]>([])

  useEffect(() => {
    let mounted = true

    async function load() {
      setLoading(true)
      setError(null)

      try {
        const [response, historico, statsData] = await Promise.all([
          getFicha(params.id),
          getHistorico().catch(() => ({ historico: [] })),
          getStats().catch(() => null),
        ])
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
          if (statsData?.segmentos_lista) setSegmentos(statsData.segmentos_lista)
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
        <span className="truncate">{item?.nome || item?.orgao || 'Analise'}</span>
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
              <SegmentoEditavel
                id={params.id}
                segmento={item.segmento}
                segmentos={segmentos}
                onSave={(seg) => setItem((prev) => prev ? { ...prev, segmento: seg } : prev)}
              />
              <ScoreBadge score={item.score || 0} breakdown={extrairJustificativas(item.ficha || '')} tooltipDirection="below" />
              {item.timestamp ? <span className="text-sm text-gray-500">{formatarData(item.timestamp)}</span> : null}
              {item.tempo_decorrido_segundos ? (
                <span className="text-sm text-gray-500" title="Tempo de análise">⏱ {formatarDuracao(item.tempo_decorrido_segundos)}</span>
              ) : null}
            </div>
            <NomeEditavel id={params.id} nome={item.nome || item.orgao || ''} />
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
