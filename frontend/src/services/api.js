/*
 * Contrato esperado da API Flask:
 *   GET /api/servidores?similar=&cargo=&uf=&orgao=&situacao=&page=&per_page=
 *     situacao: ATIVO | APOSENTADO (apenas na busca avançada)
 *     similar: padrão LIKE montado pelo frontend a partir do campo Nome
 *              ("maria silva" -> "%MARIA%SILVA%"); de preferência,
 *              ordenar com os nomes idênticos ao digitado primeiro
 *   200 -> { total, page, per_page, pages, data: [{ nome, cargo, uf, orgao, situacao, ... }] }
 *   Erros -> { erro: "mensagem" } com 400 / 404 / 429 / 504
 */
import { getJson } from "./http.js";

export function fetchServidores(params, page = 1) {
  return getJson("/api/servidores", { ...params, page });
}

export function checkHealth() {
  return getJson("/api/health");
}
