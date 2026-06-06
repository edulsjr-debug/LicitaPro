# LicitaPRO — Prompt para Codex: Implementar Frontend Next.js

## Contexto

O LicitaPRO analisa editais de licitação pública com IA.
Backend: FastAPI (Python) em `https://licitapro-dev.onrender.com` (branch dev).
Frontend: Next.js 15 na pasta `frontend/` deste repositório — deployado em Vercel:
`https://licita-humditgva-edulsjr-s-projects.vercel.app/`

Variável de ambiente no Vercel: `NEXT_PUBLIC_API_URL=https://licitapro-dev.onrender.com`

A estrutura de arquivos, tipos e API client já foram criados. Implemente os componentes e páginas.

## Stack do frontend
- Next.js 15, App Router, TypeScript
- Tailwind CSS
- `react-markdown` + `remark-gfm` para renderizar análises em Markdown
- `clsx` para classes condicionais
- API client pronto em `frontend/src/lib/api.ts`
- Tipos prontos em `frontend/src/lib/types.ts`

## Design de referência

Visual atual do app (extraído do HTML em produção):
- Fundo: `#f8f9fb`
- Cards brancos com borda `#e5e7eb`, sombra sutil
- Cor primária: `#6366f1` (indigo) — botões, links ativos, destaques
- Sidebar fixa à esquerda (desktop) com logo e navegação
- Em mobile: navbar horizontal no topo
- Estilo limpo, similar ao Linear / Vercel

---

## Layout principal

Criar `frontend/src/components/AppShell.tsx` com:

**Sidebar (desktop, 220px, fixa):**
- Logo "Licita**PRO**" no topo
- Links de navegação com ícones:
  - "Editais" `/` (ícone: lista)
  - "Novo edital" `/novo` (ícone: +)
  - "Histórico" `/historico` (ícone: relógio)
  - "Logs" `/logs` (ícone: terminal)
- Link ativo destacado com fundo indigo-50 e texto indigo-700
- Versão do app no rodapé da sidebar (buscar de `/stats`)

**Conteúdo principal:** `max-w-5xl`, padding 32px

**Mobile:** sidebar vira bottom nav ou hamburger menu

Atualizar `frontend/src/app/layout.tsx` para usar `AppShell`.

---

## Página 1: Editais / Dashboard (`/`)

`frontend/src/app/page.tsx` — `'use client'`

**Busca:** `GET /stats` e `GET /historico`

**Seção stats** (grid 4 colunas → 2 em tablet → 1 em mobile):
- "Análises hoje" com limite visual (`{analises_hoje} / {limite_diario}`)
- "Total salvo" → `historico_n`
- "Alta viabilidade" → count de score >= 75
- "Score médio" → `score_medio` com cor (verde >=70, amarelo 40-69, vermelho <40)

**Lista de editais recentes** (últimos 10):
- Cada item: órgão (bold), objeto (2 linhas, ellipsis), badge segmento, badge score, data relativa
- Clicável → `/historico/[id]`
- Link "Ver todos" → `/historico`

**Botão "Novo edital"** em destaque no header da página

---

## Página 2: Novo edital (`/novo`)

`frontend/src/app/novo/page.tsx` — `'use client'`

### Etapa 1 — Upload

**Dropzone:**
- Área de drag-and-drop para PDF, DOCX, XLSX, TXT
- Aceita múltiplos arquivos
- Lista arquivos com nome, tamanho (ex: "2,4 MB") e botão remover (x)
- Clique abre o file picker
- Estados visuais: idle, dragover (borda indigo), com arquivos

**Seletor de modo** (aparece após selecionar arquivo):
- 3 botões: Auto (padrão) | Código | IA
- Auto = parser local + fallback IA; Código = só parser; IA = direto para IA

**Botão "Analisar edital"** (full-width, indigo):
- Loading: spinner + "Analisando… pode levar até 30s"
- Chama `POST /analisar/arquivo` com FormData (campo `arquivos` + campo `modo`)

### Etapa 2 — Resultado (mesma página, sem navegar)

Quando a resposta chega:
- Botão "← Nova análise" (volta para etapa 1)
- Botão "Copiar ficha" (copia markdown para clipboard)
- Score badge grande + segmento detectado
- Renderização da `ficha` com `<FichaMarkdown>`

Criar `frontend/src/lib/utils.ts` com:
```typescript
export function extrairScore(ficha: string): number {
  const m = ficha.match(/Score[^:]*:\*?\*?\s*(\d+)\/100/) || ficha.match(/\*\*Score:\*\*\s*(\d+)/)
  return m ? Math.min(100, Math.max(0, parseInt(m[1]))) : 0
}
export function formatarData(iso: string): string // "24/05/2026 às 03:15"
export function dataRelativa(iso: string): string // "há 2 horas"
export function formatarBytes(bytes: number): string // "2,4 MB"
```

---

## Página 3: Histórico (`/historico`)

`frontend/src/app/historico/page.tsx` — `'use client'`

**Busca:** `GET /historico`

**Barra de filtros:**
- Busca por texto (orgao + objeto)
- Select: segmento (Todos + cada segmento)
- Select: score (Todos / >=70 Alta / 40-69 Média / <40 Baixa)

**Lista agrupada por dia:**
- Cabeçalho de grupo: "Hoje", "Ontem", ou data (ex: "23/05/2026")
- Cards: órgão, objeto (2 linhas), badge segmento, badge score, hora (HH:MM)
- Clique → `/historico/[id]`

**Estado vazio:** "Nenhuma análise ainda" + link para `/novo`

---

## Página 4: Detalhe (`/historico/[id]`)

`frontend/src/app/historico/[id]/page.tsx` — `'use client'`

**Busca:** `GET /historico/[id]`

**Layout:**
- Breadcrumb: Histórico → {orgão}
- Header: órgão (título), badges segmento + score, data/hora
- Card cinza com objeto em destaque
- Arquivos anexados (se houver): lista com link de download → `GET /historico/[id]/arquivos/[arquivo_id]`
- Botão "Copiar ficha"
- Renderização completa do markdown com `<FichaMarkdown>`

---

## Página 5: Logs (`/logs`)

`frontend/src/app/logs/page.tsx` — `'use client'`

**Busca:** `GET /api/logs/recent?limit=100`

Resposta: `{ log: string[], errors: string[] }`

**Layout:**
- Dois painéis: "Log geral" e "Erros"
- Cada painel: `<pre>` com fonte mono, scroll, fundo escuro (#1e1e2e) + texto claro
- Botão "Atualizar" (refetch)
- Auto-refresh a cada 30s com countdown visível

---

## Componentes a criar

### `frontend/src/components/AppShell.tsx`
Layout com sidebar + área de conteúdo — ver seção Layout acima.

### `frontend/src/components/ScoreBadge.tsx`
Recebe `score: number`.
- >=70: fundo verde-100, texto verde-700, label "Alta"
- 40-69: fundo amarelo-100, texto amarelo-700, label "Média"
- <40: fundo vermelho-100, texto vermelho-700, label "Baixa"
- Formato: "85 · Alta"

### `frontend/src/components/SegmentoBadge.tsx`
Cores por segmento:
- Saúde → verde, Educação → azul, Obras → laranja, Alimentação → amarelo
- TI → indigo, Transporte → cinza-azul, Segurança → vermelho
- Limpeza → teal, Mobiliário → marrom, Viagens → roxo, Outros → cinza

### `frontend/src/components/FichaMarkdown.tsx`
```tsx
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
```

### `frontend/src/components/Skeleton.tsx`
Retângulo cinza animado (pulse). Aceita `className`.

---

## Variável de ambiente

`NEXT_PUBLIC_API_URL` = URL da API (já referenciado em `lib/api.ts`)

## Não fazer
- Sem autenticação
- Sem bibliotecas UI externas (sem shadcn, chakra, MUI)
- Não criar backend

## Ordem sugerida
1. `AppShell.tsx` + atualizar `layout.tsx`
2. Componentes base: `ScoreBadge`, `SegmentoBadge`, `FichaMarkdown`, `Skeleton`, `lib/utils.ts`
3. Página `/novo` (core do produto)
4. Página `/historico` e `/historico/[id]`
5. Página `/` (editais/dashboard)
6. Página `/logs`
