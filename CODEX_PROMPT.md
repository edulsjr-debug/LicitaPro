# LicitaPRO — Prompt para Codex: Implementar Frontend Next.js

## Contexto

O LicitaPRO é uma aplicação que analisa editais de licitação pública usando IA.
O backend é FastAPI (Python) e está em produção em `https://licitapro-0brh.onrender.com`.
O frontend será Next.js 15 na pasta `frontend/` deste repositório.

A estrutura já foi criada. Você precisa implementar todos os componentes e páginas.

## Stack do frontend
- Next.js 15, App Router, TypeScript
- Tailwind CSS
- `react-markdown` + `remark-gfm` para renderizar o resultado da análise (Markdown)
- `clsx` para classes condicionais
- API client já pronto em `frontend/src/lib/api.ts`
- Tipos já prontos em `frontend/src/lib/types.ts`

## Design de referência

O app atual tem este visual (extraído do HTML original):
- Fundo cinza claro `#f8f9fb`
- Cards brancos com borda `#e5e7eb` e sombra sutil
- Cor primária: `#6366f1` (indigo)
- Fonte: sistema (-apple-system, Segoe UI)
- Navbar fixa com logo "Licita**PRO**" + links de navegação
- Estilo limpo, similar a Linear/Notion/Vercel

## Navbar (componente compartilhado)

Criar `frontend/src/components/Navbar.tsx`:
- Sticky no topo, fundo branco com backdrop-blur
- Logo "Licita**PRO**" (PRO em indigo)
- Links de navegação: "Dashboard" `/`, "Novo edital" `/novo`, "Histórico" `/historico`
- Link ativo destacado
- Badge com versão da API (buscar de `/stats` com `use client` + `useEffect`, opcional)

## Página 1: Dashboard (`/`)

Arquivo: `frontend/src/app/page.tsx`

**Deve ser `'use client'`** — busca dados da API no carregamento.

**Seção 1 — Cards de stats** (grid 4 colunas, 2 em mobile):
- Busca `GET /stats` da API
- Cards:
  - "Análises hoje" → `analises_hoje` (número grande)
  - "Total de análises" → `total_analises`
  - "Score médio" → `score_medio` com barra de progresso colorida (verde ≥70, amarelo 40-69, vermelho <40)
  - "Custo estimado" → `custo_usd_total` formatado como "US$ 0,0042"

**Seção 2 — Últimas análises** (as 5 mais recentes do histórico):
- Busca `GET /historico`
- Mostra cards compactos com: órgão, objeto (truncado 80 chars), segmento (badge colorido), score (badge), data relativa (ex: "há 2 horas")
- Cada card é clicável → navega para `/historico/[id]`
- Link "Ver todas" → `/historico`

**Loading state:** skeleton com animação pulse
**Erro:** mensagem amigável com botão de retry

## Página 2: Novo edital (`/novo`)

Arquivo: `frontend/src/app/novo/page.tsx`

**Deve ser `'use client'`**

**Fluxo em 2 etapas:**

### Etapa 1 — Upload/Input

**Dropzone** (componente principal):
- Área de drag-and-drop para PDF, DOCX, XLSX, TXT
- Aceita múltiplos arquivos simultaneamente
- Lista os arquivos adicionados com nome, tamanho e botão de remover
- Clique na área também abre o seletor de arquivos
- Estados visuais: idle, dragover (borda indigo, fundo indigo-50), arquivos adicionados

**Seletor de modo** (visível após adicionar arquivo):
- 3 botões: "Auto" | "Código" | "IA"
- "Auto" = selecionado por padrão (usa parser local + fallback para IA)
- "Código" = apenas parser local, sem IA
- "IA" = envia direto para IA
- Tooltip/descrição abaixo de cada opção

**Botão "Analisar edital"**:
- Visível após selecionar arquivo
- Ao clicar: chama `POST /analisar/arquivo` com os arquivos e modo
- Estado de loading: spinner + "Analisando..." (pode demorar 15-30s)

### Etapa 2 — Resultado

Quando a análise retorna, mostrar na mesma página (sem navegar):
- Botão "← Nova análise" para voltar à etapa 1
- Botão "Copiar ficha" (copia o markdown para clipboard)
- Botão "Ver no histórico" → `/historico` 
- Renderização do markdown da `ficha` usando `react-markdown` com `remark-gfm`
  - Aplicar className `ficha-md` (estilos já definidos em globals.css)
  - Renderizar tabelas, blockquotes, listas corretamente

**Formato da resposta da API:**
```typescript
{ ficha: string } // markdown da análise
```

## Página 3: Histórico (`/historico`)

Arquivo: `frontend/src/app/historico/page.tsx`

**Deve ser `'use client'`**

**Busca** `GET /historico` → retorna `{ historico: HistoricoItem[] }`

**Filtros** (barra acima da lista):
- Campo de busca por texto (filtra em orgao + objeto)
- Select de segmento (todos os segmentos + "Todos")
- Select de score (Todos / Alto ≥70 / Médio 40-69 / Baixo <40)

**Lista de análises** (cards):
Cada card contém:
- Score badge (canto superior direito, colorido)
- Órgão (título, bold)
- Objeto (2 linhas, truncado com ellipsis)
- Badge de segmento (colorido por categoria)
- Data/hora (ex: "24/05/2026 às 03:15")
- Valor estimado (se disponível)
- Clique → `/historico/[id]`

**Cores dos segmentos** (badges):
- Saúde: verde
- Educação: azul
- Obras e Infraestrutura: laranja
- Alimentação: amarelo
- Tecnologia e TI: indigo
- Transporte: cinza
- Segurança: vermelho
- Outros: cinza neutro

**Estado vazio:** mensagem "Nenhuma análise ainda" com link para `/novo`

## Página 4: Detalhe da análise (`/historico/[id]`)

Arquivo: `frontend/src/app/historico/[id]/page.tsx`

**Deve ser `'use client'`**

**Busca** `GET /historico/[id]` → retorna `HistoricoDetalhe`

**Layout:**
- Botão "← Histórico" (volta)
- Header: órgão (título grande), badge segmento, badge score, data
- Objeto em destaque (card cinza claro)
- Valor estimado
- Botão "Copiar ficha" 
- Seção da ficha completa em Markdown (`ficha-md`)

**Loading:** skeleton
**404:** mensagem "Análise não encontrada"

## Componentes a criar

### `frontend/src/components/ScoreBadge.tsx`
Recebe `score: number`. 
- ≥70 → fundo verde-100, texto verde-700, "Alta"
- 40-69 → fundo amarelo-100, texto amarelo-700, "Média"  
- <40 → fundo vermelho-100, texto vermelho-700, "Baixa"
- Formato: "85 · Alta"

### `frontend/src/components/SegmentoBadge.tsx`
Recebe `segmento: string`. Mapa de cor por segmento (ver cores acima).

### `frontend/src/components/FichaMarkdown.tsx`
Recebe `ficha: string`.
```tsx
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
Componente de skeleton para loading states. Recebe `className`.

## Variável de ambiente

`NEXT_PUBLIC_API_URL` = URL da API do Render.
Já usada em `frontend/src/lib/api.ts`.

## O que NÃO fazer
- Não criar autenticação (app é público)
- Não criar rota `/status` (já existe na API em JSON)
- Não usar bibliotecas de UI externas além das listadas (sem shadcn, sem chakra)
- Não criar backend — a API Python já existe

## Ordem sugerida de implementação
1. `Navbar.tsx`
2. `ScoreBadge.tsx`, `SegmentoBadge.tsx`, `Skeleton.tsx`, `FichaMarkdown.tsx`
3. Página `/novo` (mais importante — core do produto)
4. Página `/historico`
5. Página `/historico/[id]`
6. Página `/` (dashboard)
