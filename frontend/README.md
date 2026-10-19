# Frontend — GovData

Interface em **React + Vite** para consulta de servidores do Executivo Federal.
Consome a API Flask do backend via HTTP/HTTPS.

## Estrutura

```text
frontend/
├── nginx/default.conf.template   # nginx de produção: SPA + proxy /api → Flask
├── Dockerfile                    # build (Node) + serve (nginx)
├── .env.example                  # variáveis de ambiente do frontend
├── vite.config.js                # proxy /api em desenvolvimento (ou mock)
├── mock/                         # API simulada para testes sem backend
└── src/
    ├── config/api.js             # URL base e timeout da API
    ├── services/
    │   ├── http.js               # cliente HTTP (fetch, timeout, erros)
    │   └── api.js                # endpoints da API (/api/servidores, /api/health)
    ├── components/               # Header, SearchForm, Results
    ├── constants.js              # abas, campos e UFs
    ├── App.jsx
    ├── main.jsx
    └── styles.css
```

## Como o frontend chega à API

O navegador sempre chama caminhos relativos `/api/...`, ou seja, na mesma origem
da página, sem CORS e funcionando igual em HTTP ou HTTPS:

```text
Navegador ─/api/...─► Vite  (npm run dev :5173) ─┐
                  └─► nginx (Docker :80)         ─┴─► API Flask (:5000)
```

| Ambiente        | Quem encaminha `/api` | Destino (configurável)                     |
|-----------------|-----------------------|--------------------------------------------|
| `npm run dev`   | proxy do Vite         | `VITE_PROXY_TARGET` (padrão `http://localhost:5000`) |
| Docker / nginx  | nginx                 | `API_UPSTREAM` (padrão `http://backend:5000`) |

Para chamar a API **direto em outro domínio** (ex.: `https://api.exemplo.gov.br`),
defina `VITE_API_URL` antes do build. Nesse caso a API precisa liberar CORS para a
origem do frontend.

## Contrato esperado da API

```http
GET /api/servidores?similar=&cargo=&uf=&orgao=&situacao=&page=&per_page=
200 → { "total", "page", "per_page", "pages", "data": [{ "nome", "cargo", "uf", "orgao", "situacao", ... }] }
4xx/5xx → { "erro": "mensagem" }

# similar: o campo "Nome" vira um padrão LIKE ("maria silva" → "%MARIA%SILVA%")
# situacao: ATIVO | APOSENTADO (busca avançada)

GET /api/health
200 → { "status": "ok" }
```

Enquanto a API não existir, as buscas exibem
“API indisponível no momento” (Docker) ou “Não foi possível conectar à API” (dev).

## Testando sem a API (mock)

Enquanto o backend não existe, o próprio Vite pode responder `/api` com dados
fictícios de `mock/servidores.json`. O frontend continua fazendo requisições
HTTP reais; nada do mock entra no build de produção.

```bash
npm run dev:mock      # http://localhost:5173 com a API simulada
npm run mock:gerar    # regenera mock/servidores.json (300 servidores + casos fixos)
```

- `mock/gerar.js`: gera o JSON (sempre o mesmo resultado; `node mock/gerar.js 1000` para mais registros).
- `mock/apiMock.js`: plugin do Vite que aplica filtros, busca por nome (completo ou parcial) e paginação
  como a API real. O JSON é relido a cada requisição, então pode ser editado à mão.

| Para testar…                 | Busque por                                   |
|------------------------------|----------------------------------------------|
| Vários resultados / paginação | UF `RS`, cargo `professor`, órgão `rio grande` |
| Situação (busca avançada)    | UF `RS` + Situação `Aposentado`              |
| Resultado único (detalhe)    | Nome `TEOBALDO QUINTINO ZAMBELLI`            |
| Homônimos                    | Nome `MARIA DA SILVA`                        |
| Nome parcial                 | `MARIA SILVA`, `SANTOS` ou `JOSE CARLOS`     |
| Nenhum resultado             | Nome `NINGUEM`                               |
| Erros HTTP                   | Nome `#400`, `#404`, `#429`, `#500`, `#502`, `#504` |
| Timeout do frontend          | Nome `#lento` (demora 20 s)                  |

## Executando

```bash
# desenvolvimento
cp .env.example .env.local  
npm install
npm run dev                  # http://localhost:5173

# produção (imagem isolada)
docker build -t govdata-frontend .
docker run -p 8080:80 -e API_UPSTREAM=http://host.docker.internal:5000 govdata-frontend
```

No `docker compose` da raiz, o serviço `backend` é encontrado automaticamente
pelo nome (`http://backend:5000`).

### HTTPS

O certificado TLS fica na borda (nginx com `listen 443 ssl` ou um proxy reverso
como Traefik/Caddy na frente). O código do frontend não muda, porque as chamadas
são relativas e herdam o protocolo da página.
