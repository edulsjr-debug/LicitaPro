'use client'

import { DragEvent, useEffect, useRef, useState } from 'react'
import clsx from 'clsx'
import { analisarArquivos, getStats } from '@/lib/api'
import type { StatsResponse } from '@/lib/types'
import { extrairJustificativas, extrairScore, extrairSegmento, formatarBytes } from '@/lib/utils'
import { FichaMarkdown } from '@/components/FichaMarkdown'
import { ScoreBadge } from '@/components/ScoreBadge'
import { SegmentoBadge } from '@/components/SegmentoBadge'

export default function NovoPage() {
  const inputRef = useRef<HTMLInputElement>(null)
  const [files, setFiles] = useState<File[]>([])
  const [dragging, setDragging] = useState(false)
  const [loading, setLoading] = useState(false)
  const [progresso, setProgresso] = useState<string | null>(null)
  const [elapsed, setElapsed] = useState(0)
  const [eta, setEta] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [ficha, setFicha] = useState<string | null>(null)
  const [aviso, setAviso] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [statusIA, setStatusIA] = useState<Pick<StatsResponse, 'ia_disponivel' | 'limite_diario_atingido' | 'analises_hoje' | 'ia_quota_reset'> & { limite_diario?: number }>({
    ia_disponivel: true,
    limite_diario_atingido: false,
    analises_hoje: 0,
  })

  useEffect(() => {
    async function carregarStatus() {
      try {
        const s = await getStats()
        setStatusIA({
          ia_disponivel: s.ia_disponivel ?? true,
          limite_diario_atingido: s.limite_diario_atingido ?? false,
          analises_hoje: s.analises_hoje,
          limite_diario: s.limite_diario,
          ia_quota_reset: s.ia_quota_reset,
        })
      } catch { /* silencioso — não bloqueia a página */ }
    }
    carregarStatus()
    const t = window.setInterval(carregarStatus, 3 * 60 * 1000)
    return () => window.clearInterval(t)
  }, [])

  function addFiles(fileList: FileList | null) {
    if (!fileList) return
    const next = Array.from(fileList)
    setFiles((current) => {
      const keys = new Set(current.map((file) => `${file.name}-${file.size}-${file.lastModified}`))
      return [...current, ...next.filter((file) => !keys.has(`${file.name}-${file.size}-${file.lastModified}`))]
    })
    setError(null)
  }

  function onDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault()
    setDragging(false)
    addFiles(event.dataTransfer.files)
  }

  useEffect(() => {
    if (!loading) { setElapsed(0); setEta(null); return }
    const t = window.setInterval(() => setElapsed((s) => s + 1), 1000)
    return () => window.clearInterval(t)
  }, [loading])

  async function analisar() {
    if (!files.length || loading) return
    setLoading(true)
    setProgresso(null)
    setError(null)

    if (typeof Notification !== 'undefined' && Notification.permission === 'default') {
      await Notification.requestPermission()
    }

    try {
      const response = await analisarArquivos(files, 'auto', setProgresso, setEta)
      setFicha(response.ficha)
      setAviso(response.aviso ?? null)
      setError(null)

      if (typeof Notification !== 'undefined' && Notification.permission === 'granted') {
        const score = extrairScore(response.ficha)
        const segmento = extrairSegmento(response.ficha)
        new Notification('LicitaPRO — Análise concluída', {
          body: `Score ${score}/100 · ${segmento}`,
          icon: '/favicon.ico',
        })
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Nao foi possivel analisar o edital.'
      setError(msg)

      if (typeof Notification !== 'undefined' && Notification.permission === 'granted') {
        new Notification('LicitaPRO — Erro na análise', { body: msg, icon: '/favicon.ico' })
      }
    } finally {
      setLoading(false)
      setProgresso(null)
    }
  }

  async function copiarFicha() {
    if (!ficha) return
    await navigator.clipboard.writeText(ficha)
    setCopied(true)
    window.setTimeout(() => setCopied(false), 1800)
  }

  if (ficha) {
    return (
      <div>
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <button
            type="button"
            onClick={() => {
              setFicha(null)
              setCopied(false)
              setAviso(null)
            }}
            className="rounded-md border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50"
          >
            Nova analise
          </button>

          <button
            type="button"
            onClick={copiarFicha}
            className="rounded-md bg-brand-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-brand-700"
          >
            {copied ? 'Copiado' : 'Copiar ficha'}
          </button>
        </div>

        {aviso ? (
          <div className="mb-4 rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">
            {aviso}
          </div>
        ) : null}

        <div className="mb-5 flex flex-wrap items-center gap-3 rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <ScoreBadge score={extrairScore(ficha)} breakdown={extrairJustificativas(ficha)} />
          <SegmentoBadge segmento={extrairSegmento(ficha)} showTooltip />
        </div>

        <section className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
          <FichaMarkdown ficha={ficha} />
        </section>
      </div>
    )
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold tracking-normal text-gray-950">Novo edital</h1>
        <p className="mt-1 text-sm text-gray-600">Envie o edital para gerar a ficha de analise com Parser + IA.</p>
      </div>

      <section
        onClick={() => inputRef.current?.click()}
        onDragOver={(event) => {
          event.preventDefault()
          setDragging(true)
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={clsx(
          'cursor-pointer rounded-lg border-2 border-dashed bg-white p-8 text-center shadow-sm transition',
          dragging ? 'border-brand-500 bg-brand-50' : files.length ? 'border-brand-300' : 'border-gray-300 hover:border-brand-300'
        )}
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".pdf,.doc,.docx,.xlsx,.xls,.txt,.odt"
          className="hidden"
          onChange={(event) => {
            addFiles(event.target.files)
            event.target.value = ''
          }}
        />
        <div className="mx-auto flex h-12 w-auto max-w-fit items-center justify-center gap-1 rounded-full bg-brand-50 px-3 text-[11px] font-semibold text-brand-600">
          PDF · DOCX · XLSX · ODT · TXT
        </div>
        <h2 className="mt-4 text-base font-semibold text-gray-950">Arraste o edital ou clique para enviar</h2>
        <p className="mt-1 text-sm text-gray-600">Multiplos arquivos simultaneos</p>
      </section>

      {files.length ? (
        <section className="mt-5 rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <div className="space-y-2">
            {files.map((file) => (
              <div
                key={`${file.name}-${file.size}-${file.lastModified}`}
                className="flex items-center justify-between gap-3 rounded-md border border-gray-100 px-3 py-2"
              >
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-gray-900">{file.name}</p>
                  <p className="text-xs text-gray-500">{formatarBytes(file.size)}</p>
                </div>
                <button
                  type="button"
                  onClick={(event) => {
                    event.stopPropagation()
                    setFiles((current) => current.filter((item) => item !== file))
                  }}
                  className="flex h-8 w-8 items-center justify-center rounded-md text-lg leading-none text-gray-500 hover:bg-gray-100 hover:text-gray-900"
                  aria-label={`Remover ${file.name}`}
                >
                  x
                </button>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      {files.length ? (
        <section className="mt-5">
          {error ? (
            <div className="mb-4 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          ) : null}

          {statusIA.limite_diario_atingido ? (
            <div className="mb-4 rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">
              Limite diário atingido ({statusIA.analises_hoje}/{statusIA.limite_diario ?? 20} análises).
            </div>
          ) : null}

          <button
            type="button"
            onClick={analisar}
            disabled={loading || !!statusIA.limite_diario_atingido}
            className="flex min-h-11 w-full flex-col items-center justify-center rounded-md bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {loading ? (
              <>
                <span className="flex items-center gap-2">
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
                  {progresso ?? 'Iniciando análise…'}
                </span>
                {eta ? (
                  <span className="mt-2 h-1.5 w-full max-w-xs overflow-hidden rounded-full bg-white/20">
                    <span
                      className="block h-full rounded-full bg-white transition-all duration-1000 ease-linear"
                      style={{ width: `${Math.min(95, (elapsed / eta) * 100)}%` }}
                    />
                  </span>
                ) : null}
                <span className="mt-1 text-xs font-normal text-white/70">
                  {eta
                    ? elapsed > eta
                      ? 'Quase lá, finalizando…'
                      : `Tempo estimado: ~${eta}s — estamos refinando os dados com IA para aumentar a confiabilidade da ficha.`
                    : `${elapsed < 60 ? `${elapsed}s` : `${Math.floor(elapsed / 60)}m ${elapsed % 60}s`}${elapsed > 30 ? ' — processando, aguarde…' : ''}`}
                </span>
              </>
            ) : (
              'Analisar edital'
            )}
          </button>
        </section>
      ) : null}
    </div>
  )
}
