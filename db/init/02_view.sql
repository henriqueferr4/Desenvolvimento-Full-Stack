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
