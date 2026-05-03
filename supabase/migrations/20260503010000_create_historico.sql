create table if not exists public.historico (
  id text primary key,
  dados jsonb not null
);

create table if not exists public.historico_arquivos (
  id text primary key,
  analise_id text not null,
  ordem integer not null,
  nome_original text not null,
  mime_type text,
  tamanho_bytes integer,
  sha256 text,
  tipo_extraido text,
  chars_extraidos integer,
  storage_path text,
  bucket text,
  criado_em timestamptz default now()
);

create index if not exists idx_historico_arquivos_analise_id
  on public.historico_arquivos (analise_id, ordem);
