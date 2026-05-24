'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useEffect, useState } from 'react'
import clsx from 'clsx'
import { getStats } from '@/lib/api'

const links = [
  { href: '/', label: 'Dashboard' },
  { href: '/novo', label: 'Novo edital' },
  { href: '/historico', label: 'Historico' },
]

export function Navbar() {
  const pathname = usePathname()
  const [version, setVersion] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true

    getStats()
      .then((stats) => {
        if (mounted && stats.versao) setVersion(stats.versao)
      })
      .catch(() => {
        if (mounted) setVersion(null)
      })

    return () => {
      mounted = false
    }
  }, [])

  return (
    <header className="sticky top-0 z-40 border-b border-gray-200 bg-white/90 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link href="/" className="text-base font-semibold tracking-normal text-gray-950">
          Licita<span className="text-brand-600">PRO</span>
        </Link>

        <nav className="flex items-center gap-1">
          {links.map((link) => {
            const active =
              link.href === '/' ? pathname === '/' : pathname === link.href || pathname.startsWith(`${link.href}/`)

            return (
              <Link
                key={link.href}
                href={link.href}
                className={clsx(
                  'rounded-md px-3 py-2 text-sm font-medium transition',
                  active ? 'bg-brand-50 text-brand-700' : 'text-gray-600 hover:bg-gray-100 hover:text-gray-950'
                )}
              >
                {link.label}
              </Link>
            )
          })}
        </nav>

        <div className="hidden min-w-24 justify-end sm:flex">
          {version ? (
            <span className="rounded-full bg-gray-100 px-2.5 py-1 text-xs font-medium text-gray-600">
              API {version}
            </span>
          ) : null}
        </div>
      </div>
    </header>
  )
}
