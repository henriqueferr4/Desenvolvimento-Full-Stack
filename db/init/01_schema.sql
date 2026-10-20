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
    mes_referencia TEXT,
    valor_remuneracao DOUBLE PRECISION
);
