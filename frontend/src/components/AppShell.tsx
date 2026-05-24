'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import clsx from 'clsx'
import { getStats } from '@/lib/api'
import { Tooltip } from './Tooltip'

type IconName = 'list' | 'plus' | 'clock' | 'terminal'

const navItems: { href: string; label: string; icon: IconName }[] = [
  { href: '/', label: 'Editais', icon: 'list' },
  { href: '/novo', label: 'Novo edital', icon: 'plus' },
  { href: '/historico', label: 'Historico', icon: 'clock' },
  { href: '/logs', label: 'Logs', icon: 'terminal' },
]

const FRONT_COMMIT =
  process.env.NEXT_PUBLIC_VERCEL_GIT_COMMIT_SHA?.slice(0, 7) ?? 'local'

type ServiceStatus = {
  backOk: boolean | null
  dbOk: boolean | null
  versao: string | null
  commit: string | null
}

function Icon({ name }: { name: IconName }) {
  if (name === 'plus') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true" className="h-4 w-4">
        <path d="M12 5v14M5 12h14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      </svg>
    )
  }
  if (name === 'clock') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true" className="h-4 w-4">
        <circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" strokeWidth="2" />
        <path d="M12 7v5l3 2" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      </svg>
    )
  }
  if (name === 'terminal') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true" className="h-4 w-4">
        <path d="m7 8 4 4-4 4M13 16h4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    )
  }
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="h-4 w-4">
      <path d="M8 6h12M8 12h12M8 18h12M4 6h.01M4 12h.01M4 18h.01" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

function StatusLed({ ok, label }: { ok: boolean | null; label: string }) {
  const dot = (
    <span
      className={clsx(
        'inline-block h-2 w-2 rounded-full transition-colors',
        ok === null ? 'bg-gray-300' : ok ? 'bg-green-500' : 'bg-red-500'
      )}
    />
  )
  return (
    <Tooltip
      align="left"
      content={
        <span>
          {label}:{' '}
          {ok === null ? 'verificando…' : ok ? 'online' : 'offline'}
        </span>
      }
    >
      {dot}
    </Tooltip>
  )
}

function SidebarFooter({ status }: { status: ServiceStatus }) {
  return (
    <div className="border-t border-gray-100 px-4 py-3">
      <div className="mb-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <StatusLed ok={true} label="Frontend" />
          <StatusLed ok={status.backOk} label="Backend" />
          <StatusLed ok={status.dbOk} label="Banco" />
        </div>
        <LogoutButton />
      </div>
      <div className="space-y-0.5">
        <p className="font-mono text-[10px] text-gray-400">
          back {status.commit ?? '—'} · front {FRONT_COMMIT}
        </p>
      </div>
    </div>
  )
}

function NavLink({ href, label, icon }: { href: string; label: string; icon: IconName }) {
  const pathname = usePathname()
  const active = href === '/' ? pathname === '/' : pathname === href || pathname.startsWith(`${href}/`)

  return (
    <Link
      href={href}
      className={clsx(
        'flex min-h-10 items-center gap-3 rounded-md px-3 text-sm font-medium transition',
        active ? 'bg-brand-50 text-brand-700' : 'text-gray-600 hover:bg-gray-100 hover:text-gray-950'
      )}
    >
      <Icon name={icon} />
      <span>{label}</span>
    </Link>
  )
}

function LogoutButton({ className }: { className?: string }) {
  const router = useRouter()

  async function handleLogout() {
    await fetch('/api/auth/logout', { method: 'POST' })
    router.push('/login')
    router.refresh()
  }

  return (
    <button
      type="button"
      onClick={handleLogout}
      className={clsx(
        'flex items-center gap-2 rounded-md px-2 py-1 text-xs text-gray-500 transition hover:bg-gray-100 hover:text-gray-700',
        className
      )}
    >
      <svg viewBox="0 0 24 24" aria-hidden="true" className="h-3.5 w-3.5">
        <path
          d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      Sair
    </button>
  )
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<ServiceStatus>({
    backOk: null,
    dbOk: null,
    versao: null,
    commit: null,
  })

  useEffect(() => {
    let mounted = true

    getStats()
      .then((s) => {
        if (mounted)
          setStatus({
            backOk: true,
            dbOk: s.db_ok ?? null,
            versao: s.versao ?? null,
            commit: s.commit ?? null,
          })
      })
      .catch(() => {
        if (mounted)
          setStatus({ backOk: false, dbOk: false, versao: null, commit: null })
      })

    return () => {
      mounted = false
    }
  }, [])

  return (
    <div className="min-h-screen bg-[#f8f9fb] pb-16 md:pb-0 md:pl-[220px]">
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-[220px] border-r border-gray-200 bg-white md:flex md:flex-col">
        <div className="flex h-16 items-center px-5">
          <Link href="/" className="text-base font-semibold tracking-normal text-gray-950">
            Licita<span className="text-brand-600">PRO</span>
          </Link>
        </div>

        <nav className="flex flex-1 flex-col gap-1 px-3">
          {navItems.map((item) => (
            <NavLink key={item.href} {...item} />
          ))}
        </nav>

        <SidebarFooter status={status} />
      </aside>

      <header className="sticky top-0 z-30 border-b border-gray-200 bg-white/90 backdrop-blur md:hidden">
        <div className="flex h-14 items-center justify-between px-4">
          <Link href="/" className="text-base font-semibold text-gray-950">
            Licita<span className="text-brand-600">PRO</span>
          </Link>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <StatusLed ok={true} label="Frontend" />
              <StatusLed ok={status.backOk} label="Backend" />
              <StatusLed ok={status.dbOk} label="Banco" />
            </div>
            <LogoutButton />
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">{children}</main>

      <nav className="fixed inset-x-0 bottom-0 z-40 grid grid-cols-4 border-t border-gray-200 bg-white md:hidden">
        {navItems.map((item) => (
          <MobileNavLink key={item.href} {...item} />
        ))}
      </nav>
    </div>
  )
}

function MobileNavLink({ href, label, icon }: { href: string; label: string; icon: IconName }) {
  const pathname = usePathname()
  const active = href === '/' ? pathname === '/' : pathname === href || pathname.startsWith(`${href}/`)

  return (
    <Link
      href={href}
      className={clsx(
        'flex min-h-14 flex-col items-center justify-center gap-1 text-[11px] font-medium',
        active ? 'text-brand-700' : 'text-gray-500'
      )}
    >
      <Icon name={icon} />
      <span>{label}</span>
    </Link>
  )
}
