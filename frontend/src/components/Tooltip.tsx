'use client'

import clsx from 'clsx'

export function Tooltip({
  children,
  content,
  className,
}: {
  children: React.ReactNode
  content: React.ReactNode
  className?: string
}) {
  return (
    <div className={clsx('group/tip relative inline-flex', className)}>
      {children}
      <div className="pointer-events-none absolute bottom-full left-1/2 z-50 mb-2.5 hidden w-60 -translate-x-1/2 group-hover/tip:block">
        <div className="rounded-xl bg-gray-900 px-3.5 py-3 text-xs leading-5 text-gray-100 shadow-2xl">
          {content}
        </div>
        <div className="absolute left-1/2 top-full -mt-px -translate-x-1/2 border-4 border-transparent border-t-gray-900" />
      </div>
    </div>
  )
}
