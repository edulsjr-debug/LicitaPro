-- Tabela de logs persistentes (sobrevive a deploys no Render)
-- Rodar no SQL Editor do Supabase: https://supabase.com/dashboard/project/_/sql

CREATE TABLE IF NOT EXISTS public.logs (
  id        bigserial primary key,
  criado_em timestamptz not null default now(),
  nivel     text        not null,
  mensagem  text        not null,
  request_id text
);

CREATE INDEX IF NOT EXISTS logs_criado_em_idx ON public.logs (criado_em DESC);

-- Row Level Security: apenas service_role pode gravar
ALTER TABLE public.logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role full access"
  ON public.logs
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- Limpeza automática: apaga logs com mais de 30 dias
-- (opcional — rodar como cron no Supabase ou manualmente)
-- DELETE FROM public.logs WHERE criado_em < now() - interval '30 days';
