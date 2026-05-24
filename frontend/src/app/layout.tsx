import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'LicitaPRO',
  description: 'Analise inteligente de editais de licitacao',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  )
}
