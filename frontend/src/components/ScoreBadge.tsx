import clsx from 'clsx'

function scoreMeta(score: number) {
  if (score >= 70) {
    return { label: 'Alta', className: 'bg-green-100 text-green-700 ring-green-200' }
  }

  if (score >= 40) {
    return { label: 'M\u00e9dia', className: 'bg-yellow-100 text-yellow-700 ring-yellow-200' }
  }

  return { label: 'Baixa', className: 'bg-red-100 text-red-700 ring-red-200' }
}

export function ScoreBadge({ score }: { score: number }) {
  const meta = scoreMeta(score)

  return (
    <span
      className={clsx(
        'inline-flex shrink-0 items-center rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset',
        meta.className
      )}
    >
      {Math.round(score)} <span className="mx-1 text-current/50">&middot;</span> {meta.label}
    </span>
  )
}
