# pg-http-proxy

Proxy HTTP -> PostgreSQL usado pelos workflows do n8n do projeto
[zscan-infra](https://github.com/eajdias/zscan-infra) (endpoints `/query` e `/batch`).

## API

| Endpoint | Descrição |
|---|---|
| `POST /query` | Executa um SQL: `{sql, params?, database?}` → `{columns, rows, rowcount}` (SELECT) ou `{columns: [], rows: [], rowcount}` (INSERT/UPDATE/DELETE, commita) |
| `POST /batch` | Executa várias queries: `{queries: [{sql, params?, database?}]}` → `{results: [{ok, ...} ou {ok: false, error}]}` |
| `GET /health` | Healthcheck → `{status: "ok"}` |

Exemplo:

```bash
curl -s http://localhost:5433/query \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT id, name FROM clients LIMIT 5", "database": "zscan_app"}'
```

## Variáveis de ambiente

| Variável | Default | Obrigatória |
|---|---|---|
| `PG_PASSWORD` | — | **sim** (falha no boot se ausente) |
| `PG_HOST` | `databases-central` | não |
| `PG_PORT` | `5432` | não |
| `PG_USER` | `postgres` | não |
| `PG_DATABASE` | `zscan_app` | não |

O database pode ser sobrescrito por request (campo `database` da query).

## Build e execução local

```bash
docker build -t pg-http-proxy:latest .
docker run --rm -p 5433:5433 -e PG_PASSWORD=... pg-http-proxy:latest
```

Testes (stdlib, sem dependências):

```bash
python -m unittest test_server -v
```

## Deploy no zscan-infra

A imagem NÃO é publicada em registro público; o deploy nas VPSs usa build
local + transporte:

```bash
docker save pg-http-proxy:latest | gzip | ssh <vps> "gunzip | docker load && docker tag pg-http-proxy:latest pg-http-proxy:latest"
```

O compose de destino (`templates/pg-http-proxy/` no zscan-infra) injeta
`PG_PASSWORD` via `.env` (nunca hardcoded no código).