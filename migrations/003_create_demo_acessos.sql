-- Tabela de controle de acesso à demo pública
-- Rodar no SQL Editor do Supabase: https://supabase.com/dashboard/project/_/sql

CREATE TABLE IF NOT EXISTS public.demo_acessos (
  id               TEXT PRIMARY KEY,       -- "ip:<addr>" ou "uid:<uuid>"
  tipo             TEXT NOT NULL,          -- 'ip' | 'uid'
  usos             INTEGER DEFAULT 0,
  primeiro_acesso  TIMESTAMPTZ DEFAULT now(),
  ultimo_acesso    TIMESTAMPTZ DEFAULT now(),
  ultimo_ip        TEXT,
  tentativa_burla  BOOLEAN DEFAULT false,
  lead_nome        TEXT,
  lead_contato     TEXT,                   -- whatsapp ou email
  bonus_liberado   BOOLEAN DEFAULT false
);

CREATE INDEX IF NOT EXISTS demo_acessos_tipo_idx ON public.demo_acessos (tipo);

ALTER TABLE public.demo_acessos ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role full access"
  ON public.demo_acessos FOR ALL TO service_role
  USING (true) WITH CHECK (true);
