import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'LicitaPRO',
  description: 'Análise inteligente de editais de licitação',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  )
}
