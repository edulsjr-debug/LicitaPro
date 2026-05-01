# Deploy gratuito 24/7 no Oracle Always Free

Este e o caminho recomendado para substituir o Render sem reescrever o LicitaPRO. A aplicacao atual e FastAPI/Python, processa upload de PDF/DOCX/XLSX e precisa de um processo web tradicional; por isso ela encaixa melhor em uma VM gratuita do que em Workers/serverless.

## Arquitetura

- Oracle Cloud Always Free: VM Ubuntu ARM `VM.Standard.A1.Flex`
- Docker Compose: app FastAPI + Caddy
- Caddy: reverse proxy e HTTPS automatico quando `APP_HOST` for um dominio valido
- Supabase: banco principal via `DATABASE_URL`
- Fallback local: `historico.json` persistido em volume Docker quando `DATABASE_URL` estiver vazio

## 1. Criar a VM

1. No Oracle Cloud, crie uma instancia Ubuntu ARM Always Free.
2. Shape sugerido: `VM.Standard.A1.Flex`, com 1 OCPU e 6 GB RAM para comecar.
3. Libere as portas 80 e 443 na security list ou network security group.
4. Acesse via SSH.

Referencia oficial: https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm

## 2. Instalar Docker no Ubuntu

Use o guia oficial do Docker para Ubuntu:

https://docs.docker.com/engine/install/ubuntu/

Depois habilite o usuario atual para usar Docker sem `sudo`:

```bash
sudo usermod -aG docker $USER
newgrp docker
docker --version
docker compose version
```

## 3. Subir o LicitaPRO

```bash
git clone https://github.com/edulsjr-debug/LicitaPro.git
cd LicitaPro
cp .env.example .env
nano .env
```

Preencha no `.env`:

```bash
APP_HOST=licitapro.seudominio.com.br
OPENAI_API_KEY=
OPENROUTER_API_KEY=
GROQ_API_KEY=
GROQ_API_KEY2=
DATABASE_URL=
```

Se ainda nao tiver dominio apontado, use temporariamente:

```bash
APP_HOST=:80
```

Suba os containers:

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f licitapro
```

Teste:

```bash
curl http://127.0.0.1:8000/healthz
curl http://SEU_IP_PUBLICO/healthz
```

## 4. DNS e HTTPS

Para HTTPS automatico:

1. Crie um registro `A` apontando o dominio para o IP publico da VM.
2. Altere `.env`:

```bash
APP_HOST=licitapro.seudominio.com.br
```

3. Reinicie:

```bash
docker compose up -d
```

O Caddy emite e renova o certificado automaticamente.

Referencias oficiais:

- Reverse proxy: https://caddyserver.com/docs/caddyfile/directives/reverse_proxy
- HTTPS automatico: https://caddyserver.com/docs/automatic-https

## 5. Atualizar deploy

```bash
cd LicitaPro
git pull
docker compose up -d --build
docker compose logs -f licitapro
```

## 6. Backup rapido

Se usar Supabase, o historico principal fica no banco.

Se usar fallback local sem Supabase, exporte o volume:

```bash
docker run --rm -v licitapro_licitapro_data:/data -v "$PWD":/backup alpine tar czf /backup/licitapro-data.tgz -C /data .
```

## Observacoes

- Isto evita hibernacao do Render free, porque a aplicacao fica rodando como processo permanente na VM.
- Nao e "garantia absoluta": todo provedor gratuito tem limites e disponibilidade de capacidade. A Oracle documenta recursos Always Free, mas a disponibilidade da shape ARM pode variar por regiao.
- Para producao real, mantenha `DATABASE_URL` no Supabase para nao depender apenas de arquivo local.
