'use client'

import { DragEvent, useRef, useState } from 'react'
import clsx from 'clsx'
import { analisarArquivos } from '@/lib/api'
import type { Modo } from '@/lib/types'
import { extrairJustificativas, extrairScore, extrairSegmento, formatarBytes } from '@/lib/utils'
import { FichaMarkdown } from '@/components/FichaMarkdown'
import { ScoreBadge } from '@/components/ScoreBadge'
import { SegmentoBadge } from '@/components/SegmentoBadge'

const modos: { value: Modo; label: string; description: string }[] = [
  { value: 'auto', label: 'Auto', description: 'Parser local com fallback para IA.' },
  { value: 'parser', label: 'Codigo', description: 'Somente parser local, sem IA.' },
  { value: 'ia', label: 'IA', description: 'Analise direta pelo modelo de IA.' },
]

export default function NovoPage() {
  const inputRef = useRef<HTMLInputElement>(null)
  const [files, setFiles] = useState<File[]>([])
  const [modo, setModo] = useState<Modo>('auto')
  const [dragging, setDragging] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [ficha, setFicha] = useState<string | null>(null)
  const [aviso, setAviso] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

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

  async function analisar() {
    if (!files.length || loading) return
    setLoading(true)
    setError(null)

    if (typeof Notification !== 'undefined' && Notification.permission === 'default') {
      await Notification.requestPermission()
    }

    try {
      const response = await analisarArquivos(files, modo)
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
        <p className="mt-1 text-sm text-gray-600">Envie PDF, DOCX, XLSX ou TXT para gerar a ficha de analise.</p>
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
          accept=".pdf,.docx,.xlsx,.xls,.txt"
          className="hidden"
          onChange={(event) => {
            addFiles(event.target.files)
            event.target.value = ''
          }}
        />
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-brand-50 text-sm font-semibold text-brand-600">
          PDF
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
          <div className="grid gap-3 sm:grid-cols-3">
            {modos.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => setModo(option.value)}
                className={clsx(
                  'rounded-lg border bg-white p-4 text-left shadow-sm transition',
                  modo === option.value ? 'border-brand-500 ring-2 ring-brand-100' : 'border-gray-200 hover:border-gray-300'
                )}
              >
                <span className="block text-sm font-semibold text-gray-950">{option.label}</span>
                <span className="mt-1 block text-xs leading-5 text-gray-600">{option.description}</span>
              </button>
            ))}
          </div>

          {error ? (
            <div className="mt-4 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          ) : null}

          <button
            type="button"
            onClick={analisar}
            disabled={loading}
            className="mt-5 flex min-h-11 w-full items-center justify-center rounded-md bg-brand-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
                Analisando... pode levar ate 30s
              </span>
            ) : (
              'Analisar edital'
            )}
          </button>
        </section>
      ) : null}
    </div>
  )
}
