CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE IF NOT EXISTS aposentados (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    cpf VARCHAR(14),
    matricula_servidor BIGINT,
    nome_orgao TEXT,
    sigla_orgao VARCHAR(20),
    codigo_orgao_superior VARCHAR(10),
    cargo TEXT,
    classe VARCHAR(5),
    padrao VARCHAR(5),
    referencia VARCHAR(5),
    nivel VARCHAR(5),
    tipo_aposentadoria VARCHAR(30),
    fundamentacao_inatividade VARCHAR(50),
    nome_diploma_legal VARCHAR(70),
    "Dt ocorrencia inatividade" TEXT,
    ocorrencia_ingresso VARCHAR(60),
    "Dt ingresso servico publico" TEXT,
    valor_rendimento_liquido DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS carreiras_cargos (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(60) NOT NULL,
    cpf VARCHAR(14),
    codigo_carreira VARCHAR(10),
    descricao_cargo_emprego VARCHAR(60),
    uf_upag VARCHAR(2),
    denominacao_orgao_atuacao VARCHAR(60),
    mes_referencia VARCHAR(2),
    valor_remuneracao DOUBLE PRECISION
);

CREATE OR REPLACE VIEW vw_servidores AS
SELECT
    id,
    nome,
    cpf,
    cargo,
    NULL::VARCHAR(2) AS uf,
    nome_orgao AS orgao,
    sigla_orgao,
    'APOSENTADO' AS situacao_vinculo,
    "Dt ocorrencia inatividade"::TEXT AS data_inatividade,
    "Dt ingresso servico publico"::TEXT AS data_ingresso_servico_publico,
    valor_rendimento_liquido AS remuneracao
FROM aposentados
UNION ALL
SELECT
    id,
    nome,
    cpf,
    descricao_cargo_emprego AS cargo,
    uf_upag AS uf,
    denominacao_orgao_atuacao AS orgao,
    NULL::VARCHAR(20) AS sigla_orgao,
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