'use client'

import { useEffect, useState } from 'react'
import { getLogs, reclassificar } from '@/lib/api'
import { Skeleton } from '@/components/Skeleton'

function LogPanel({ title, lines }: { title: string; lines: string[] }) {
  return (
    <section className="min-h-0 rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <h2 className="mb-3 text-sm font-semibold text-gray-950">{title}</h2>
      <pre className="max-h-[520px] min-h-64 overflow-auto rounded-md bg-[#1e1e2e] p-4 text-xs leading-6 text-gray-100">
        {lines.length ? lines.join('\n') : 'Sem registros.'}
      </pre>
    </section>
  )
}

export default function LogsPage() {
  const [log, setLog] = useState<string[]>([])
  const [errors, setErrors] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [countdown, setCountdown] = useState(30)
  const [reclassMsg, setReclassMsg] = useState<string | null>(null)
  const [reclassLoading, setReclassLoading] = useState(false)

  async function load() {
    setError(null)

    try {
      const response = await getLogs(100)
      setLog(response.log || [])
      setErrors(response.errors || [])
      setCountdown(30)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Nao foi possivel carregar os logs.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  useEffect(() => {
    const timer = window.setInterval(() => {
      setCountdown((current) => {
        if (current <= 1) {
          load()
          return 30
        }
        return current - 1
      })
    }, 1000)

    return () => window.clearInterval(timer)
  }, [])

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal text-gray-950">Logs</h1>
          <p className="mt-1 text-sm text-gray-600">Atualizacao automatica em {countdown}s.</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            disabled={reclassLoading}
            onClick={async () => {
              setReclassLoading(true)
              setReclassMsg(null)
              try {
                const r = await reclassificar()
                setReclassMsg(`${r.atualizados} de ${r.total} registros corrigidos.`)
              } catch {
                setReclassMsg('Erro ao reclassificar.')
              } finally {
                setReclassLoading(false)
              }
            }}
            className="rounded-md border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 disabled:opacity-60"
          >
            {reclassLoading ? 'Corrigindo…' : 'Corrigir histórico'}
          </button>
          <button
            type="button"
            onClick={() => { setLoading(true); load() }}
            className="rounded-md bg-brand-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-brand-700"
          >
            Atualizar
          </button>
        </div>
      </div>

      {reclassMsg ? <div className="mb-4 rounded-md border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">{reclassMsg}</div> : null}
      {error ? <div className="mb-4 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}

      {loading ? (
        <div className="grid gap-4 lg:grid-cols-2">
          <Skeleton className="h-96" />
          <Skeleton className="h-96" />
        </div>
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          <LogPanel title="Log geral" lines={log} />
          <LogPanel title="Erros" lines={errors} />
        </div>
      )}
    </div>
  )
}
