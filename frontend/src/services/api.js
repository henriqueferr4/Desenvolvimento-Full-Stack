import { ApiError, getJson } from "./http.js";

export async function fetchServidores(params, page = 1, signal) {
  const body = await getJson("/api/servidores", { ...params, page }, { signal });
  // protege contra respostas 200 que não são da API (ex.: HTML de um proxy mal configurado)
  if (!body || !Array.isArray(body.data)) throw new ApiError("Resposta inesperada da API.", 502);
  return body;
}

export function checkHealth(signal) {
  return getJson("/api/health", {}, { signal });
}
