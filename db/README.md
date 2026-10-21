# Módulo de Banco de Dados (PostgreSQL)

Este diretório contém a infraestrutura do sistema de consulta de servidores do Poder Executivo Federal: modelagem relacional, scripts de inicialização, índices de busca e o pipeline de ETL (extração, transformação e carga) das bases públicas de servidores ativos e aposentados.

---

## 1. Requisitos atendidos

- PostgreSQL 15 em ambiente conteinerizado (Docker).
- Tratamento e preparação de dados do Portal Brasileiro de Dados Abertos (https://dados.gov.br/dados/conjuntos-dados/gestao-de-pessoas-executivo-federal--aposentados e https://dados.gov.br/dados/conjuntos-dados/gestao-de-pessoas-executivo-federal---carreiras--cargos).
- Busca exata e busca por similaridade em qualquer posição.
- Conversão das datas legadas do SIAPE (DDMMAAAA, sem barras e sem zeros à esquerda) para o tipo nativo DATE.

---

## 2. Estrutura de diretórios

```text
db/
├── init/
│   ├── 01_schema.sql            # extensão pg_trgm e tabelas
│   ├── 02_view.sql              # view unificada `servidores` (também usada pelo popular.py)
│   └── 03_indexes.sql           # índices de busca (também usados pelo popular.py)
├── dados_brutos/                # (ignorado no Git) arquivos baixados do portal (.csv / .txt)
├── dados_tratados/              # (ignorado no Git) CSVs tratados em UTF-8 (cache)
├── popular.py                   # ETL: detecção, limpeza e carga em massa via COPY
├── requirements.txt             # dependências do ETL (psycopg v3, o mesmo driver do backend)
└── README.md                    # documentação
```

---

## 3. Subindo o banco

Os scripts de `db/init/` são executados **apenas na primeira criação do volume** `postgres_data`. Para recriar o banco do zero (necessário após alterar o schema):

```bash
docker compose down -v
docker compose up -d db
```

```bash
python db/popular.py                      # carga completa (pede confirmação)
python db/popular.py --limite 50          # somente 50 linhas por tabela (teste)
python db/popular.py --forcar-conversao   # refaz os CSVs tratados
python db/popular.py --sim                # sem confirmação (scripts / CI)
```

Configuração padrão do container (definida no `docker-compose.yml`):

| Parâmetro | Valor |
|---|---|
| Imagem | `postgres:15-alpine` |
| Banco | `POSTGRES_DB` (padrão `executivo_federal_db`) |
| Usuário | `POSTGRES_USER` (padrão `postgres`) |
| Senha | `POSTGRES_PASSWORD` (obrigatória, no `.env` da raiz) |
| Porta | `5432`, publicada apenas em `127.0.0.1` |
| Healthcheck | `pg_isready` a cada 5s |

---

## 4. Modelagem relacional

### Tabela `aposentados`

Mapeia as 18 colunas originais do conjunto de aposentados.

| Coluna | Tipo | Observação |
|---|---|---|
| `id` | `SERIAL` | Chave primária |
| `nome` | `TEXT` | Obrigatório |
| `cpf` | `TEXT` | Mascarado na origem |
| `matricula_servidor` | `BIGINT` | |
| `nome_orgao`, `sigla_orgao`, `codigo_orgao_superior` | `TEXT` | |
| `cargo`, `classe`, `padrao`, `referencia`, `nivel` | `TEXT` | |
| `tipo_aposentadoria`, `fundamentacao_inatividade`, `nome_diploma_legal` | `TEXT` | |
| `"Dt ocorrencia inatividade"` | `TEXT`¹ | |
| `ocorrencia_ingresso` | `TEXT` | |
| `"Dt ingresso servico publico"` | `TEXT`¹ | |
| `valor_rendimento_liquido` | `DOUBLE PRECISION` | |

¹ Guardadas como `TEXT` no formato `DDMMYYYY` (sem zeros à esquerda); o `popular.py` já descarta datas inexistentes. A view `servidores` converte para `DD/MM/YYYY`.

### Tabela `carreiras_cargos` (servidores ativos)

Mapeia as 8 colunas originais do conjunto de carreiras e cargos.

| Coluna | Tipo |
|---|---|
| `id` | `SERIAL` (PK) |
| `nome` | `TEXT` (obrigatório) |
| `cpf`, `codigo_carreira`, `descricao_cargo_emprego`, `denominacao_orgao_atuacao` | `TEXT` |
| `uf_upag` | `VARCHAR(2)` |
| `mes_referencia` | `TEXT` |
| `valor_remuneracao` | `DOUBLE PRECISION` |

### View unificada `servidores`

Consolida ativos e aposentados por meio de `UNION ALL`, sem duplicar dados físicos.

| Coluna | Origem (aposentados / ativos) |
|---|---|
| `id` | `id` da tabela de origem (**não é único na view**) |
| `chave` | `'A-' \|\| id` / `'C-' \|\| id` (**única na view**) |
| `nome`, `cpf` | `nome`, `cpf` |
| `cargo` | `cargo` / `descricao_cargo_emprego` |
| `uf` | `NULL` / `uf_upag` |
| `orgao` | `nome_orgao` / `denominacao_orgao_atuacao` |
| `sigla_orgao` | `sigla_orgao` / `NULL` |
| `situacao_vinculo` | `'APOSENTADO'` / `'ATIVO'` |
| `data_inatividade` | data de inatividade em `DD/MM/YYYY` / `NULL` |
| `data_ingresso_servico_publico` | data de ingresso em `DD/MM/YYYY` / `NULL` |
| `remuneracao` | `valor_rendimento_liquido` / `valor_remuneracao` |

Observações sobre a view:
- As datas são retornadas como texto `DD/MM/YYYY`.
- `uf` só existe para ativos (a base de aposentados não informa UF) e `sigla_orgao` só existe para aposentados.
- `id` se repete entre as duas origens; use `chave` para identificar um registro.

---

## 5. Índices e tipos de busca

A extensão `pg_trgm` habilita índices GIN para busca textual em qualquer posição e por similaridade.

| Índice | Tabela | Tipo | Finalidade |
|---|---|---|---|
| `idx_aposentados_nome_trgm` | `aposentados` | GIN `gin_trgm_ops` | nome (contém / similaridade) |
| `idx_aposentados_nome_exato` | `aposentados` | B-Tree `UPPER(nome)` | nome exato |
| `idx_aposentados_cargo_trgm` | `aposentados` | GIN `gin_trgm_ops` | cargo |
| `idx_aposentados_orgao_trgm` | `aposentados` | GIN `gin_trgm_ops` | órgão |
| `idx_carreiras_nome_trgm` | `carreiras_cargos` | GIN `gin_trgm_ops` | nome (contém / similaridade) |
| `idx_carreiras_nome_exato` | `carreiras_cargos` | B-Tree `UPPER(nome)` | nome exato |
| `idx_carreiras_cargo_trgm` | `carreiras_cargos` | GIN `gin_trgm_ops` | cargo |
| `idx_carreiras_orgao_trgm` | `carreiras_cargos` | GIN `gin_trgm_ops` | órgão |
| `idx_carreiras_uf` | `carreiras_cargos` | B-Tree `UPPER(uf_upag)` | UF |

### Consultas que aproveitam os índices

```sql
-- Nome exato
SELECT * FROM servidores WHERE UPPER(nome) = UPPER('JOAO DA SILVA');
--Exemplo de uso:
docker exec -it postgres_db psql -U postgres -d executivo_federal_db -c "SELECT nome, cargo, orgao FROM servidores WHERE UPPER(nome) = UPPER('Maria da Silva');"

-- Nome contém (qualquer posição)
SELECT * FROM servidores WHERE nome ILIKE '%silva%';
-- Exemplo de uso:
docker exec -it postgres_db psql -U postgres -d executivo_federal_db -c "SELECT nome, cargo, orgao FROM servidores WHERE nome ILIKE '%MARIA%SILVA%';"
docker exec -it postgres_db psql -U postgres -d executivo_federal_db -c "SELECT nome, cargo, uf, orgao, remuneracao FROM servidores WHERE uf = 'DF' AND cargo ILIKE '%ANALISTA%' LIMIT 10;"

-- Similaridade de nome
SELECT *, similarity(nome, 'joao silva') AS score
FROM servidores
WHERE nome % 'joao silva'
ORDER BY score DESC;
--Exemplo de uso:
docker exec -it postgres_db psql -U postgres -d executivo_federal_db -c "SELECT nome, cargo, similarity(nome, 'maria silva') AS score FROM servidores WHERE nome % 'maria silva' ORDER BY score DESC LIMIT 10;"
```

---

## 6. Conversão de datas

As bases do SIAPE trazem datas no formato `DDMMAAAA`, sem separadores e sem zero à esquerda (ex.: `1012020` para 01/01/2020). Elas ficam no banco como `TEXT`, e a view `servidores` as converte na leitura:

```sql
CASE WHEN "Dt ocorrencia inatividade" ~ '^[0-9]{7,8}$'
     THEN TO_CHAR(TO_DATE(LPAD("Dt ocorrencia inatividade", 8, '0'), 'DDMMYYYY'), 'DD/MM/YYYY')
END
```

Durante a limpeza, o `popular.py` valida cada data; datas inexistentes (ex.: `31022020`) ou zeradas são gravadas como `NULL`, evitando que um único valor inválido derrube a view (o `TO_DATE` do PostgreSQL rejeita datas impossíveis).

---

## 7. Pipeline de ETL (`popular.py`)

### Preparação

Coloque os arquivos brutos (`.csv` ou `.txt`) em `db/dados_brutos/`. O script resolve os diretórios a partir da própria pasta `db/`, então pode ser executado de qualquer lugar.

### Execução

```bash
python db/popular.py                      # carga completa (pede confirmação)
python db/popular.py --limite 50          # somente 50 linhas por tabela (teste)
python db/popular.py --forcar-conversao   # refaz os CSVs tratados
python db/popular.py --sim                # sem confirmação
```

### O que o script faz

1. **Classificação automática** de cada arquivo bruto pelo número de colunas da primeira linha: 15 ou mais colunas é tratado como *aposentados*; de 8 a 14 colunas, como *carreiras e cargos*; outros formatos são ignorados com um aviso.
2. **Limpeza e padronização** (leitura em `latin1`, saída em UTF-8):
   - lê o CSV respeitando campos entre aspas; remove bytes nulos, BOM, linhas vazias, linhas incompletas, linhas sem nome e cabeçalhos repetidos;
   - converte valores monetários (`1.234,56` para `1234.56`) e a matrícula (somente dígitos);
   - valida as datas (seção 6);
   - em *carreiras*, limita `uf_upag` a 2 caracteres e preserva `mes_referencia` como veio.
3. **Consolidação**: vários arquivos brutos do mesmo tipo são unidos em um único CSV tratado (`aposentados_tratado.csv` e `carreiras_tratado.csv`).
4. **Cache**: o CSV tratado só é refeito se não existir, estiver vazio, ou se algum arquivo bruto for mais recente (ou com `--forcar-conversao`).
5. **Carga em massa**, tudo em **uma única transação** (se algo falhar, nada muda e a view continua no ar):
   - remove a view e os índices;
   - executa `TRUNCATE ... RESTART IDENTITY` nas duas tabelas (**substitui os dados existentes, inclusive a seed**; por isso o script pede confirmação, ou `--sim`);
   - carrega os dados com `COPY`;
   - recria a view `servidores` e os índices a partir de `db/init/02_view.sql` e `03_indexes.sql`;
   - executa `ANALYZE` nas duas tabelas.

### Variáveis de ambiente

| Variável | Padrão |
|---|---|
| `DB_HOST` | `localhost` |
| `DB_PORT` | `5432` |
| `POSTGRES_DB` | `executivo_federal_db` |
| `POSTGRES_USER` | `postgres` |
| `POSTGRES_PASSWORD` | *(obrigatória)* |

O script lê o `.env` da raiz do projeto (se `python-dotenv` estiver instalado).

---
