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

- 🌐 **HTML**
- 🎨 **CSS**
- ⚡ **JavaScript**
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
│   └── ...
│
├── docker-compose.yml
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
