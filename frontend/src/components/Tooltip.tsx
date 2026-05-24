'use client'

import clsx from 'clsx'

export function Tooltip({
  children,
  content,
  className,
  align = 'center',
}: {
  children: React.ReactNode
  content: React.ReactNode
  className?: string
  align?: 'center' | 'left' | 'right'
}) {
  return (
    <div className={clsx('group/tip relative inline-flex', className)}>
      {children}
      <div
        className={clsx(
          'pointer-events-none absolute bottom-full z-50 mb-2.5 hidden w-52 group-hover/tip:block',
          align === 'center' && 'left-1/2 -translate-x-1/2',
          align === 'left' && 'left-0',
          align === 'right' && 'right-0'
        )}
      >
        <div className="rounded-xl bg-gray-900 px-3.5 py-3 text-xs leading-5 text-gray-100 shadow-2xl">
          {content}
        </div>
        <div
          className={clsx(
            'absolute top-full -mt-px border-4 border-transparent border-t-gray-900',
            align === 'center' && 'left-1/2 -translate-x-1/2',
            align === 'left' && 'left-3',
            align === 'right' && 'right-3'
          )}
        />
      </div>
    </div>
  )
}
