'use client'

import { useEffect, useState } from 'react'
import { getLogs, reclassificar, resegmentarIA } from '@/lib/api'
import { getClientErrors, clearClientErrors, type ClientError } from '@/lib/errorStore'
import { Skeleton } from '@/components/Skeleton'

function LogPanel({ title, lines }: { title: string; lines: string[] }) {
  return (
    <section className="min-h-0 rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <h2 className="mb-3 text-sm font-semibold text-gray-950">{title}</h2>
      <pre className="max-h-[520px] min-h-64 overflow-auto rounded-md bg-[#1e1e2e] p-4 text-xs leading-6 text-gray-100">
        {lines.length ? lines.join('\n') : '# Sem registros nesta sessão.\n# Os logs são reiniciados a cada deploy no Render (disco efêmero).\n# Novos registros aparecem após as próximas análises.'}
      </pre>
    </section>
  )
}

function ClientErrorPanel({ errors, onClear }: { errors: ClientError[]; onClear: () => void }) {
  if (!errors.length) return null
  return (
    <section className="rounded-lg border border-red-200 bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-red-700">Erros do cliente ({errors.length})</h2>
        <button
          type="button"
          onClick={onClear}
          className="text-xs text-gray-400 hover:text-gray-600"
        >
          Limpar
        </button>
      </div>
      <div className="max-h-[400px] overflow-auto space-y-2">
        {[...errors].reverse().map((e, i) => (
          <div key={i} className="rounded-md bg-red-50 px-3 py-2 font-mono text-[11px] leading-5">
            <span className="text-gray-400">{new Date(e.ts).toLocaleString('pt-BR')}</span>
            {' '}
            <span className="font-semibold text-red-600">{e.method}</span>
            {' '}
            <span className="break-all text-gray-700">{e.url}</span>
            {e.status ? <span className="ml-1 text-orange-600"> [{e.status}]</span> : null}
            <div className="mt-0.5 text-red-800">{e.message}</div>
          </div>
        ))}
      </div>
    </section>
  )
}

export default function LogsPage() {
  const [log, setLog] = useState<string[]>([])
  const [errors, setErrors] = useState<string[]>([])
  const [clientErrors, setClientErrors] = useState<ClientError[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [countdown, setCountdown] = useState(30)
  const [reclassMsg, setReclassMsg] = useState<string | null>(null)
  const [reclassLoading, setReclassLoading] = useState(false)
  const [resegMsg, setResegMsg] = useState<string | null>(null)
  const [resegLoading, setResegLoading] = useState(false)

  function refreshClientErrors() {
    setClientErrors(getClientErrors())
  }

  async function load() {
    setError(null)
    refreshClientErrors()
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
            disabled={resegLoading}
            onClick={async () => {
              setResegLoading(true)
              setResegMsg(null)
              try {
                const r = await resegmentarIA()
                setResegMsg(`${r.atualizados} de ${r.total} editais resegmentados pela IA.`)
              } catch {
                setResegMsg('Erro ao resegmentar.')
              } finally {
                setResegLoading(false)
              }
            }}
            className="rounded-md border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 disabled:opacity-60"
          >
            {resegLoading ? 'Resegmentando…' : 'Resegmentar com IA'}
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
      {resegMsg ? <div className="mb-4 rounded-md border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-700">{resegMsg}</div> : null}
      {error ? <div className="mb-4 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}

      <ClientErrorPanel
        errors={clientErrors}
        onClear={() => { clearClientErrors(); setClientErrors([]) }}
      />

      {clientErrors.length > 0 ? <div className="mb-4" /> : null}

      {loading ? (
        <div className="grid gap-4 lg:grid-cols-2">
          <Skeleton className="h-96" />
          <Skeleton className="h-96" />
        </div>
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          <LogPanel title="Log geral" lines={log} />
          <LogPanel title="Erros do servidor" lines={errors} />
        </div>
      )}
    </div>
  )
}
