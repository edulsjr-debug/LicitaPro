import clsx from 'clsx'
import { Tooltip } from './Tooltip'

const segmentoClasses: Record<string, string> = {
  Saude: 'bg-green-100 text-green-700 ring-green-200',
  Educacao: 'bg-blue-100 text-blue-700 ring-blue-200',
  'Obras e Infraestrutura': 'bg-orange-100 text-orange-700 ring-orange-200',
  Obras: 'bg-orange-100 text-orange-700 ring-orange-200',
  Alimentacao: 'bg-yellow-100 text-yellow-800 ring-yellow-200',
  'Tecnologia e TI': 'bg-brand-100 text-brand-700 ring-brand-200',
  TI: 'bg-brand-100 text-brand-700 ring-brand-200',
  Transporte: 'bg-slate-100 text-slate-700 ring-slate-200',
  Seguranca: 'bg-red-100 text-red-700 ring-red-200',
  Limpeza: 'bg-teal-100 text-teal-700 ring-teal-200',
  'Limpeza e Conservacao': 'bg-teal-100 text-teal-700 ring-teal-200',
  Mobiliario: 'bg-amber-100 text-amber-800 ring-amber-200',
  'Mobiliario e Escritorio': 'bg-amber-100 text-amber-800 ring-amber-200',
  Viagens: 'bg-purple-100 text-purple-700 ring-purple-200',
  'Viagens e Passagens': 'bg-purple-100 text-purple-700 ring-purple-200',
  'Eventos e Capacitacao': 'bg-purple-100 text-purple-700 ring-purple-200',
  Outros: 'bg-gray-100 text-gray-700 ring-gray-200',
}

function normalizeSegmento(segmento: string) {
  return segmento
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/Ãº/g, 'u')
    .replace(/Ã§/g, 'c')
    .replace(/Ã£/g, 'a')
    .replace(/Ã¡/g, 'a')
    .replace(/Ã©/g, 'e')
    .replace(/Ã³/g, 'o')
}

export function SegmentoBadge({ segmento, showTooltip = false }: { segmento: string; showTooltip?: boolean }) {
  const normalized = normalizeSegmento(segmento || 'Outros')
  const className = segmentoClasses[normalized] ?? segmentoClasses.Outros

  const badge = (
    <span
      className={clsx(
        'inline-flex shrink-0 cursor-default items-center rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset',
        className
      )}
    >
      {segmento || 'Outros'}
    </span>
  )

  if (!showTooltip) return badge

  return (
    <Tooltip
      content={
        <div>
          <p className="mb-1.5 font-semibold text-white">Segmento</p>
          <p className="text-gray-300">
            Detectado automaticamente pelo parser. Afeta até 40 dos 100 pontos no score de
            viabilidade.
          </p>
        </div>
      }
    >
      {badge}
    </Tooltip>
  )
}
