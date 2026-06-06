# LicitaPRO — Codex Task: Dashboard de Produtividade

## Objetivo

Enriquecer a página principal (`/`) com métricas de produtividade, pipeline financeiro e oportunidades em destaque. O dashboard atual já existe e funciona — apenas adicionar/substituir o que está especificado abaixo, sem quebrar nada.

---

## Contexto técnico

- **Arquivo a modificar:** `frontend/src/app/(app)/page.tsx`
- **Arquivo utilitários:** `frontend/src/lib/utils.ts` (adicionar `parseValorBRL` e `formatarMoedaBRL`)
- **Tipos:** `frontend/src/lib/types.ts` — não alterar
- **Sem mudança no backend** — todos os dados vêm de `GET /stats` e `GET /historico` que já são chamados no `useEffect`

---

## Passo 1 — Adicionar utilitários em `frontend/src/lib/utils.ts`

Adicionar ao final do arquivo (não remover nada):

```typescript
/** "R$ 2.000.000,00" → 2000000  |  retorna 0 se não parsear */
export function parseValorBRL(valor: string | undefined): number {
  if (!valor) return 0
  const m = valor.match(/([\d.,]+)/)
  if (!m) return 0
  // remove pontos de milhar, troca vírgula decimal por ponto
  const n = parseFloat(m[1].replace(/\./g, '').replace(',', '.'))
  return Number.isFinite(n) ? n : 0
}

/** 2000000 → "R$ 2,0 mi"  |  9500000000 → "R$ 9,5 bi" */
export function formatarMoedaBRL(valor: number): string {
  if (valor === 0) return 'R$ 0'
  if (valor >= 1_000_000_000) return `R$ ${(valor / 1_000_000_000).toFixed(1).replace('.', ',')} bi`
  if (valor >= 1_000_000) return `R$ ${(valor / 1_000_000).toFixed(1).replace('.', ',')} mi`
  if (valor >= 1_000) return `R$ ${(valor / 1_000).toFixed(0)} mil`
  return `R$ ${valor.toFixed(0)}`
}
```

---

## Passo 2 — Modificar `frontend/src/app/(app)/page.tsx`

### 2a. Imports — adicionar os dois novos utilitários

```typescript
import { dataRelativa, parseValorBRL, formatarMoedaBRL } from '@/lib/utils'
```

### 2b. Novos `useMemo` — adicionar após as constantes existentes (após `topSegmento`)

```typescript
// Tempo economizado: estimativa de 60 min por edital
const minutosSalvos = totalSalvo * 60
const tempoEconomizado = minutosSalvos >= 60
  ? `${Math.floor(minutosSalvos / 60)}h${minutosSalvos % 60 > 0 ? ` ${minutosSalvos % 60}min` : ''}`
  : `${minutosSalvos} min`

// Custo por análise
const custoPorAnalise = totalSalvo > 0 && custoTotal > 0
  ? `$${(custoTotal / totalSalvo).toFixed(4)}`
  : null

// Valor total avaliado (parseia "R$ X.XXX.XXX,XX" de cada item do histórico)
const valorTotalAvaliado = useMemo(
  () => historico.reduce((sum, item) => sum + parseValorBRL(item.valor), 0),
  [historico]
)

// Valor só dos de alta viabilidade (score >= 75)
const valorAltaViabilidade = useMemo(
  () => historico.filter((item) => (item.score || 0) >= 75).reduce((sum, item) => sum + parseValorBRL(item.valor), 0),
  [historico]
)

// Taxa de aproveitamento (% de alta viabilidade)
const taxaAproveitamento = totalSalvo > 0 ? Math.round((altaViabilidade / totalSalvo) * 100) : 0

// Top 3 oportunidades (maior score, score > 0)
const topOportunidades = useMemo(
  () =>
    [...historico]
      .filter((item) => (item.score || 0) > 0)
      .sort((a, b) => (b.score || 0) - (a.score || 0))
      .slice(0, 3),
  [historico]
)
```

> **Atenção:** `valorTotalAvaliado` e `valorAltaViabilidade` já usam `useMemo` no bloco acima — não envolver novamente. `tempoEconomizado`, `custoPorAnalise` e `taxaAproveitamento` são derivações simples que NÃO precisam de `useMemo`.

### 2c. Grid de cards — substituir a `<section>` do grid atual

O grid atual tem 6 cards em `lg:grid-cols-3`. Substituir por **duas linhas de grid**:

**Linha 1 — Produtividade (4 colunas em desktop):**

```tsx
<section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
  {/* Card 1: Análises hoje — mantém exatamente igual ao atual */}
  <StatCard
    label="Análises hoje"
    value={
      <>
        {stats?.analises_hoje ?? 0}
        <span className="ml-1 text-base font-medium text-gray-400">/ {limiteDiario}</span>
      </>
    }
    sub="Limite diário — reseta à meia-noite"
  >
    <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-gray-100">
      <div className="h-full rounded-full bg-brand-500 transition-all" style={{ width: `${Math.min(100, ((stats?.analises_hoje ?? 0) / limiteDiario) * 100)}%` }} />
    </div>
  </StatCard>

  {/* Card 2: Tempo economizado */}
  <StatCard
    label="Tempo economizado"
    value={totalSalvo > 0 ? tempoEconomizado : '—'}
    sub={totalSalvo > 0 ? `${totalSalvo} editais × ~60 min de leitura manual` : 'Nenhum edital analisado ainda'}
  />

  {/* Card 3: Custo por análise */}
  <StatCard
    label="Custo por análise"
    value={custoPorAnalise ?? '—'}
    sub={custoPorAnalise ? `Total acumulado: $${custoTotal.toFixed(4)}` : 'Nenhum uso de IA ainda'}
  />

  {/* Card 4: Taxa de aproveitamento */}
  <StatCard
    label="Taxa de aproveitamento"
    value={totalSalvo > 0 ? `${taxaAproveitamento}%` : '—'}
    sub={totalSalvo > 0 ? `${altaViabilidade} de alta viabilidade (≥ 75 pts)` : 'Sem dados'}
  >
    {totalSalvo > 0 ? (
      <div className="mt-3 flex h-2 overflow-hidden rounded-full">
        <div className="bg-green-500 transition-all" style={{ width: `${(altaViabilidade / totalSalvo) * 100}%` }} title={`Alta: ${altaViabilidade}`} />
        <div className="bg-yellow-400 transition-all" style={{ width: `${(mediaViabilidade / totalSalvo) * 100}%` }} title={`Média: ${mediaViabilidade}`} />
        <div className="flex-1 bg-red-400" title={`Baixa: ${baixaViabilidade}`} />
      </div>
    ) : null}
  </StatCard>
</section>
```

**Linha 2 — Pipeline financeiro (3 colunas em desktop):** adicionar logo após o fechamento da seção acima:

```tsx
<section className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
  {/* Card 5: Valor total avaliado */}
  <StatCard
    label="Valor total avaliado"
    value={valorTotalAvaliado > 0 ? formatarMoedaBRL(valorTotalAvaliado) : '—'}
    sub={valorTotalAvaliado > 0 ? `Soma dos contratos analisados` : 'Nenhum valor identificado ainda'}
  />

  {/* Card 6: Oportunidades qualificadas (valor das de alta viabilidade) */}
  <StatCard
    label="Oportunidades qualificadas"
    value={valorAltaViabilidade > 0 ? formatarMoedaBRL(valorAltaViabilidade) : '—'}
    sub={valorAltaViabilidade > 0 ? `Contratos com score ≥ 75` : `${altaViabilidade} editais de alta viabilidade`}
  />

  {/* Card 7: Score médio — mantém exatamente igual ao atual */}
  <StatCard label="Score médio" value={scoreMedio || '—'}>
    <div className="mt-3 h-2 overflow-hidden rounded-full bg-gray-100">
      <div className={clsx('h-full rounded-full transition-all', scoreColor(scoreMedio))} style={{ width: `${Math.min(100, scoreMedio)}%` }} />
    </div>
    {totalSalvo > 0 ? (
      <div className="mt-2 flex gap-3 text-xs text-gray-500">
        <span className="text-green-600">{altaViabilidade} alta</span>
        <span className="text-yellow-600">{mediaViabilidade} média</span>
        <span className="text-red-500">{baixaViabilidade} baixa</span>
      </div>
    ) : null}
  </StatCard>
</section>
```

### 2d. Seção "Top oportunidades" — inserir ANTES da seção "Recentes"

Adicionar esta seção logo antes do `<section className="mt-8">` (seção Recentes):

```tsx
{topOportunidades.length > 0 ? (
  <section className="mt-8">
    <div className="mb-3 flex items-center justify-between">
      <h2 className="text-lg font-semibold text-gray-950">Top oportunidades</h2>
      <span className="text-xs text-gray-400">Maiores scores do histórico</span>
    </div>
    <div className="grid gap-3 sm:grid-cols-3">
      {topOportunidades.map((item, idx) => (
        <Link
          key={item.id}
          href={`/historico/${item.id}`}
          className="relative rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition hover:border-brand-200 hover:shadow-md"
        >
          <div className="mb-2 flex items-start justify-between gap-2">
            <span className="text-xs font-bold text-gray-300">#{idx + 1}</span>
            <ScoreBadge score={item.score || 0} />
          </div>
          <h3 className="truncate text-sm font-semibold text-gray-950">{item.nome || item.orgao || 'Sem identificação'}</h3>
          <p className="mt-1 line-clamp-2 text-xs leading-5 text-gray-500">{item.objeto || 'Objeto não informado'}</p>
          <div className="mt-2">
            <SegmentoBadge segmento={item.segmento} />
          </div>
        </Link>
      ))}
    </div>
  </section>
) : null}
```

### 2e. Seção "Recentes" — manter exatamente igual, só mudar o título

Alterar `<h2>` de `"Recentes"` para `"Últimas análises"` e manter todo o resto sem alteração.

---

## O que NÃO alterar

- Componentes `StatCard`, `ScoreBadge`, `SegmentoBadge`, `Skeleton` — sem modificação
- A lógica de `load()`, `useEffect`, `setStats`, `setHistorico` — sem modificação
- Os cards removidos da grade (Custo IA acumulado, Segmento mais analisado, Provedores de IA) ficam **deletados** do JSX — os dados ainda são calculados caso sejam necessários futuramente, mas não precisam mais aparecer na tela
- `frontend/src/lib/types.ts` — sem modificação
- Todos os outros arquivos do projeto — sem modificação

---

## Resultado esperado

Página `/` com:
1. **Linha 1** (4 cols): Análises hoje | Tempo economizado | Custo por análise | Taxa de aproveitamento
2. **Linha 2** (3 cols): Valor total avaliado | Oportunidades qualificadas | Score médio
3. **Seção Top oportunidades**: 3 cards lado a lado com os maiores scores
4. **Seção Últimas análises**: lista dos 10 mais recentes (idêntica à atual)
