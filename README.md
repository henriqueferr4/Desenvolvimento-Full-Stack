# Desenvolvimento-Full-Stack

# 🔎 Consulta de Servidores do Executivo Federal

Aplicação **Full Stack** desenvolvida para consulta de dados públicos de servidores ativos e aposentados do Poder Executivo Federal.

O sistema permite realizar buscas por **nome, cargo/profissão, estado (UF) e instituição/órgão**, além de buscas combinadas e por similaridade de nomes.

Os dados utilizados são provenientes do **Portal Brasileiro de Dados Abertos**.

---

## 🛠️ Tecnologias e Ferramentas

### Back-end

- 🐍 **Python**
- 🌶️ **Flask** — desenvolvimento da API REST
- 🚀 **Gunicorn (WSGI)** — servidor da aplicação
- 📦 **JSON** — comunicação entre API e Front-end

### Banco de Dados

- 🐘 **PostgreSQL**
- Consultas indexadas
- Busca por similaridade
- Tratamento e preparação dos dados públicos

### Front-end

- ⚛️ **React 19** + **Vite**
- 🎨 **CSS**
- 🌐 **nginx** — serve o build e encaminha `/api` para o Flask
- Requisições **HTTP/HTTPS** para consumo da API

### Infraestrutura e Desenvolvimento

- 🐳 **Docker**
- 🐳 **Docker Compose**
- 📦 **Dockerfile**
- 🌿 **Git**
- 🐙 **GitHub**

---

## 🏗️ Arquitetura

A aplicação é dividida em três serviços principais:

```text
┌──────────────┐
│  Front-end   │
└──────┬───────┘
       │ HTTP
       ▼
┌──────────────┐
│  Flask API   │
│  + Gunicorn  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  PostgreSQL  │
└──────────────┘
```

## 📁 Estrutura do Projeto

```text
projeto/
│
├── backend/
│   ├── Dockerfile
│   └── ...
│
├── frontend/
│   ├── Dockerfile
│   └── ...
│
├── db/
│   ├── init/        # schema, view e índices (executados na criação do volume)
│   └── popular.py   # ETL dos CSVs do portal de dados abertos
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🔍 Funcionalidades

O sistema deverá permitir:

- 🔎 Busca exata por nome;
- 🔤 Busca por similaridade de nome;
- 💼 Busca por cargo ou profissão;
- 📍 Busca por estado (UF);
- 🏛️ Busca por instituição ou órgão;
- 🔗 Combinação de múltiplos filtros;
- 📄 Paginação dos resultados;
- 📦 Retorno dos dados através de API REST em formato JSON.

---

## ▶️ Como executar

```bash
cp .env .env            # defina POSTGRES_PASSWORD (a senha não pode ter @ / : ? #)
docker compose up -d --build    # banco + API (gunicorn) + frontend (nginx) em http://localhost

# carga dos dados (baixe os CSVs do portal para db/dados_brutos/ antes)
pip install -r db/requirements.txt
python db/popular.py            # pede confirmação: substitui os dados existentes
```

Detalhes do banco e do ETL em [`db/README.md`](db/README.md); do frontend (incluindo o
modo mock, que dispensa backend e banco) em [`frontend/README.md`](frontend/README.md).

### API

```http
GET /api/servidores?similar=&nome=&cargo=&uf=&orgao=&situacao=&page=&per_page=
200 → { "total", "page", "per_page", "pages", "data": [{ "chave", "nome", "cargo", "uf", "orgao", "situacao", ... }] }
400/500/503/504 → { "erro": "mensagem", "erros": ["..."] }

GET /api/health → { "status": "ok" }
```

- `similar`: padrão `LIKE` (`%` é curinga; `_` e `\` são tratados como texto); nomes idênticos ao digitado vêm primeiro e o teto é de 100 resultados.
- `nome`: igualdade exata (sem diferenciar maiúsculas); `cargo` e `orgao`: contêm o texto; `uf` e `situacao` (`ATIVO` | `APOSENTADO`): igualdade.
- `per_page`: 1 a 50 (padrão 20). Informe ao menos um critério de busca.
- A base de aposentados não tem UF; filtrar por `uf` retorna apenas servidores ativos.

---
