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
│   ├── 01_schema.sql            # extensão, tabelas, view unificada e índices
├── dados_brutos/                # (ignorado no Git) arquivos baixados do portal (.csv / .txt)
├── dados_tratados/              # (ignorado no Git) CSVs tratados em UTF-8 (cache)
├── popular.py                   # ETL: detecção, limpeza e carga em massa via COPY
├── requirements.txt             # dependências do ETL (psycopg2-binary)
└── README.md                    # documentação
```

---

## 3. Subindo o banco

```bash
docker compose up -d db
```

Os scripts de `db/init/` são executados **apenas na primeira criação do volume** `postgres_data`. Para recriar o banco do zero (necessário após alterar o schema):

```bash
docker compose down -v
docker compose up -d db
```

--Requisito para rodar o script que popula o banco
```bash
pip install -r db/requirements.txt
```

```bash
python db/popular.py                      # carga completa
python db/popular.py --limite 50          # somente 50 linhas por tabela (teste)
python db/popular.py --forcar-conversao   # refaz os CSVs tratados
```

Configuração padrão do container (definida no `docker-compose.yml`):

| Parâmetro | Valor |
|---|---|
| Imagem | `postgres:15-alpine` |
| Banco | `executivo_federal_db` |
| Usuário | `postgres` |
| Porta | `5432` |
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
| `"Dt ocorrencia inatividade"` | `DATE` após a carga¹ | |
| `ocorrencia_ingresso` | `TEXT` | |
| `"Dt ingresso servico publico"` | `DATE` após a carga¹ | |
| `valor_rendimento_liquido` | `DOUBLE PRECISION` | |

¹ No schema inicial essas colunas são `TEXT` (formato bruto `DDMMYYYY`). O `popular.py` as converte para `DATE` durante a carga.

### Tabela `carreiras_cargos` (servidores ativos)

Mapeia as 8 colunas originais do conjunto de carreiras e cargos.

| Coluna | Tipo |
|---|---|
| `id` | `SERIAL` (PK) |
| `nome` | `TEXT` (obrigatório) |
| `cpf`, `codigo_carreira`, `descricao_cargo_emprego`, `denominacao_orgao_atuacao` | `TEXT` |
| `uf_upag` | `VARCHAR(2)` |
| `mes_referencia` | `VARCHAR(2)` |
| `valor_remuneracao` | `DOUBLE PRECISION` |

### View unificada `vw_servidores`

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
- As datas são sempre retornadas como texto `DD/MM/YYYY`, tanto com o schema inicial (colunas `TEXT`) quanto após a carga completa (colunas `DATE`).
- `uf` só existe para ativos e `sigla_orgao` só existe para aposentados.
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
SELECT * FROM vw_servidores WHERE UPPER(nome) = UPPER('JOAO DA SILVA');
--Exemplo de uso:
docker exec -it postgres_db psql -U postgres -d executivo_federal_db -c "SELECT nome, cargo, orgao FROM vw_servidores WHERE UPPER(nome) = UPPER('Maria da Silva');"

-- Nome contém (qualquer posição)
SELECT * FROM vw_servidores WHERE nome ILIKE '%silva%';
-- Exemplo de uso:
docker exec -it postgres_db psql -U postgres -d executivo_federal_db -c "SELECT nome, cargo, orgao FROM vw_servidores WHERE nome ILIKE '%MARIA%SILVA%';"
docker exec -it postgres_db psql -U postgres -d executivo_federal_db -c "SELECT nome, cargo, uf, orgao, remuneracao FROM vw_servidores WHERE uf = 'DF' AND cargo ILIKE '%ANALISTA%' LIMIT 10;"

-- Similaridade de nome
SELECT *, similarity(nome, 'joao silva') AS score
FROM vw_servidores
WHERE nome % 'joao silva'
ORDER BY score DESC;
--Exemplo de uso:
docker exec -it postgres_db psql -U postgres -d executivo_federal_db -c "SELECT nome, cargo, similarity(nome, 'maria silva') AS score FROM vw_servidores WHERE nome % 'maria silva' ORDER BY score DESC LIMIT 10;"

---

## 6. Conversão de datas

As bases do SIAPE trazem datas no formato `DDMMAAAA`, sem separadores e sem zero à esquerda (ex.: `1012020` para 01/01/2020). A conversão para `DATE` usa:

```sql
ALTER TABLE aposentados
  ALTER COLUMN "Dt ocorrencia inatividade" TYPE DATE
  USING to_date(lpad("Dt ocorrencia inatividade"::text, 8, '0'), 'DDMMYYYY');

ALTER TABLE aposentados
  ALTER COLUMN "Dt ingresso servico publico" TYPE DATE
  USING to_date(lpad("Dt ingresso servico publico"::text, 8, '0'), 'DDMMYYYY');
```

O `popular.py` aplica essa conversão automaticamente após carregar os aposentados. Antes disso, durante a limpeza, ele valida cada data; datas inexistentes (ex.: `31022020`) ou zeradas são gravadas como `NULL`, evitando que um único valor inválido interrompa a conversão.

---

## 7. Pipeline de ETL (`popular.py`)

### Preparação

```bash
pip install -r db/requirements.txt
```

Coloque os arquivos brutos (`.csv` ou `.txt`) em `db/dados_brutos/`. O script resolve os diretórios a partir da própria pasta `db/`, então pode ser executado de qualquer lugar.

### Execução

```bash
python db/popular.py                      # carga completa
python db/popular.py --limite 50          # somente 50 linhas por tabela (teste)
python db/popular.py --forcar-conversao   # refaz os CSVs tratados
```

### O que o script faz

1. **Classificação automática** de cada arquivo bruto pelo número de colunas da primeira linha: 15 ou mais colunas é tratado como *aposentados*; de 7 a 14 colunas, como *carreiras e cargos*.
2. **Limpeza e padronização** (leitura em `latin1`, saída em UTF-8):
   - remove bytes nulos, linhas vazias, linhas incompletas, linhas sem nome e cabeçalhos repetidos;
   - converte valores monetários (`1.234,56` para `1234.56`) e a matrícula (somente dígitos);
   - valida as datas (seção 6);
   - em *carreiras*, limita `uf_upag` e `mes_referencia` a 2 caracteres.
3. **Consolidação**: vários arquivos brutos do mesmo tipo são unidos em um único CSV tratado (`aposentados_tratado.csv` e `carreiras_tratado.csv`).
4. **Cache**: o CSV tratado só é refeito se não existir, estiver vazio, ou se algum arquivo bruto for mais recente (ou com `--forcar-conversao`).
5. **Carga em massa**:
   - remove a view e os índices;
   - executa `TRUNCATE ... RESTART IDENTITY` nas duas tabelas (**substitui os dados existentes, inclusive a seed**);
   - carrega os dados com `COPY`;
   - converte as datas para `DATE`;
   - recria a view `vw_servidores` e todos os índices;
   - executa `ANALYZE` nas duas tabelas.

### Variáveis de ambiente

| Variável | Padrão |
|---|---|
| `DB_HOST` | `localhost` |
| `DB_PORT` | `5432` |
| `POSTGRES_DB` | `executivo_federal_db` |
| `POSTGRES_USER` | `postgres` |
| `POSTGRES_PASSWORD` | `postgres_password` |

---
