'use client'

import clsx from 'clsx'

export function Tooltip({
  children,
  content,
  className,
  align = 'center',
  direction = 'above',
}: {
  children: React.ReactNode
  content: React.ReactNode
  className?: string
  align?: 'center' | 'left' | 'right'
  direction?: 'above' | 'below'
}) {
  const above = direction === 'above'
  return (
    <div className={clsx('group/tip relative inline-flex', className)}>
      {children}
      <div
        className={clsx(
          'pointer-events-none absolute z-50 hidden w-52 group-hover/tip:block',
          above ? 'bottom-full mb-2.5' : 'top-full mt-2.5',
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
            'absolute border-4 border-transparent',
            above ? 'top-full -mt-px border-t-gray-900' : 'bottom-full -mb-px border-b-gray-900',
            align === 'center' && 'left-1/2 -translate-x-1/2',
            align === 'left' && 'left-3',
            align === 'right' && 'right-3'
          )}
        />
      </div>
    </div>
  )
}
