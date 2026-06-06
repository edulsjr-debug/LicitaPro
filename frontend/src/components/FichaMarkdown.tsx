'use client'

import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export function FichaMarkdown({ ficha }: { ficha: string }) {
  return (
    <div className="ficha-md">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{ficha}</ReactMarkdown>
    </div>
  )
}
