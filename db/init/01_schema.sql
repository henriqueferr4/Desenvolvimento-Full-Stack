CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE IF NOT EXISTS aposentados (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    cpf TEXT,
    matricula_servidor BIGINT,
    nome_orgao TEXT,
    sigla_orgao TEXT,
    codigo_orgao_superior TEXT,
    cargo TEXT,
    classe TEXT,
    padrao TEXT,
    referencia TEXT,
    nivel TEXT,
    tipo_aposentadoria TEXT,
    fundamentacao_inatividade TEXT,
    nome_diploma_legal TEXT,
    "Dt ocorrencia inatividade" TEXT,
    ocorrencia_ingresso TEXT,
    "Dt ingresso servico publico" TEXT,
    valor_rendimento_liquido DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS carreiras_cargos (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    cpf TEXT,
    codigo_carreira TEXT,
    descricao_cargo_emprego TEXT,
    uf_upag VARCHAR(2),
    denominacao_orgao_atuacao TEXT,
    mes_referencia VARCHAR(2),
    valor_remuneracao DOUBLE PRECISION
);

CREATE OR REPLACE VIEW servidores AS
SELECT
    id,
    'A-' || id::TEXT AS chave,
    nome,
    cpf,
    cargo,
    NULL::TEXT AS uf,
    nome_orgao AS orgao,
    sigla_orgao,
    'APOSENTADO' AS situacao_vinculo,
    CASE WHEN "Dt ocorrencia inatividade" ~ '^[0-9]{7,8}$'
         THEN TO_CHAR(TO_DATE(LPAD("Dt ocorrencia inatividade", 8, '0'), 'DDMMYYYY'), 'DD/MM/YYYY')
    END AS data_inatividade,
    CASE WHEN "Dt ingresso servico publico" ~ '^[0-9]{7,8}$'
         THEN TO_CHAR(TO_DATE(LPAD("Dt ingresso servico publico", 8, '0'), 'DDMMYYYY'), 'DD/MM/YYYY')
    END AS data_ingresso_servico_publico,
    valor_rendimento_liquido AS remuneracao
FROM aposentados
UNION ALL
SELECT
    id,
    'C-' || id::TEXT AS chave,
    nome,
    cpf,
    descricao_cargo_emprego AS cargo,
    uf_upag::TEXT AS uf,
    denominacao_orgao_atuacao AS orgao,
    NULL::TEXT AS sigla_orgao,
    'ATIVO' AS situacao_vinculo,
    NULL::TEXT AS data_inatividade,
    NULL::TEXT AS data_ingresso_servico_publico,
    valor_remuneracao AS remuneracao
FROM carreiras_cargos;

CREATE INDEX IF NOT EXISTS idx_aposentados_nome_trgm ON aposentados USING gin (nome gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_aposentados_nome_exato ON aposentados (UPPER(nome));
CREATE INDEX IF NOT EXISTS idx_aposentados_cargo_trgm ON aposentados USING gin (cargo gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_aposentados_orgao_trgm ON aposentados USING gin (nome_orgao gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_carreiras_nome_trgm ON carreiras_cargos USING gin (nome gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_carreiras_nome_exato ON carreiras_cargos (UPPER(nome));
CREATE INDEX IF NOT EXISTS idx_carreiras_cargo_trgm ON carreiras_cargos USING gin (descricao_cargo_emprego gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_carreiras_orgao_trgm ON carreiras_cargos USING gin (denominacao_orgao_atuacao gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_carreiras_uf ON carreiras_cargos (UPPER(uf_upag));
