import clsx from 'clsx'
import { Tooltip } from './Tooltip'

function scoreMeta(score: number) {
  if (score >= 70) {
    return { label: 'Alta', className: 'bg-green-100 text-green-700 ring-green-200' }
  }
  if (score >= 40) {
    return { label: 'Média', className: 'bg-yellow-100 text-yellow-700 ring-yellow-200' }
  }
  return { label: 'Baixa', className: 'bg-red-100 text-red-700 ring-red-200' }
}

export function ScoreBadge({ score, breakdown, tooltipDirection = 'above' }: { score: number; breakdown?: string[]; tooltipDirection?: 'above' | 'below' }) {
  const meta = scoreMeta(score)

  const badge = (
    <span
      className={clsx(
        'inline-flex shrink-0 cursor-default items-center rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset',
        meta.className
      )}
    >
      {Math.round(score)}
      <span className="mx-1 opacity-50">&middot;</span>
      {meta.label}
    </span>
  )

  if (!breakdown?.length) return badge

  return (
    <Tooltip
      direction={tooltipDirection}
      content={
        <div>
          <p className="mb-2 font-semibold text-white">Score de Viabilidade</p>
          <ul className="space-y-1.5">
            {breakdown.map((line) => (
              <li key={line} className="text-gray-300">
                {line}
              </li>
            ))}
          </ul>
          <p className="mt-2.5 border-t border-white/10 pt-2 text-gray-400">
            Máximo: 100 pts (40 + 25 + 20 + 15)
          </p>
        </div>
      }
    >
      {badge}
    </Tooltip>
  )
}
