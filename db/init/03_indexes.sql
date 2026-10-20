CREATE INDEX IF NOT EXISTS idx_aposentados_nome_trgm ON aposentados USING gin (nome gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_aposentados_nome_exato ON aposentados (UPPER(nome));
CREATE INDEX IF NOT EXISTS idx_aposentados_cargo_trgm ON aposentados USING gin (cargo gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_aposentados_orgao_trgm ON aposentados USING gin (nome_orgao gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_carreiras_nome_trgm ON carreiras_cargos USING gin (nome gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_carreiras_nome_exato ON carreiras_cargos (UPPER(nome));
CREATE INDEX IF NOT EXISTS idx_carreiras_cargo_trgm ON carreiras_cargos USING gin (descricao_cargo_emprego gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_carreiras_orgao_trgm ON carreiras_cargos USING gin (denominacao_orgao_atuacao gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_carreiras_uf ON carreiras_cargos (UPPER(uf_upag));
