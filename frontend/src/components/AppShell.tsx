'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useEffect, useState } from 'react'
import clsx from 'clsx'
import { getStats } from '@/lib/api'

type IconName = 'list' | 'plus' | 'clock' | 'terminal'

const navItems: { href: string; label: string; icon: IconName }[] = [
  { href: '/', label: 'Editais', icon: 'list' },
  { href: '/novo', label: 'Novo edital', icon: 'plus' },
  { href: '/historico', label: 'Historico', icon: 'clock' },
  { href: '/logs', label: 'Logs', icon: 'terminal' },
]

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

export function AppShell({ children }: { children: React.ReactNode }) {
  const [version, setVersion] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true

    getStats()
      .then((stats) => {
        if (mounted) setVersion(stats.versao || stats.commit || null)
      })
      .catch(() => {
        if (mounted) setVersion(null)
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

        <div className="border-t border-gray-100 p-4 text-xs text-gray-500">
          {version ? <span>API {version}</span> : <span>API indisponivel</span>}
        </div>
      </aside>

      <header className="sticky top-0 z-30 border-b border-gray-200 bg-white/90 backdrop-blur md:hidden">
        <div className="flex h-14 items-center justify-between px-4">
          <Link href="/" className="text-base font-semibold text-gray-950">
            Licita<span className="text-brand-600">PRO</span>
          </Link>
          {version ? <span className="text-xs text-gray-500">API {version}</span> : null}
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
