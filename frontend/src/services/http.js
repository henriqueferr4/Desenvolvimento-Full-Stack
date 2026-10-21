import { API_BASE_URL, API_TIMEOUT_MS } from "../config/api.js";

const MESSAGES = {
  400: "Parâmetros de busca inválidos.",
  404: "Nenhum servidor encontrado para esta busca.",
  408: "Tempo de busca excedido.",
  429: "Muitas requisições. Aguarde alguns segundos e tente de novo.",
  500: "Erro interno do servidor.",
  501: "Recurso ainda não implementado na API.",
  502: "API indisponível no momento. Tente novamente mais tarde.",
  503: "API indisponível no momento. Tente novamente mais tarde.",
  504: "Tempo de busca excedido no servidor.",
};

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

// GET em JSON com timeout e mensagens de erro padronizadas.
// `signal` (opcional) cancela a requisição; nesse caso o AbortError original é relançado.
export async function getJson(path, params = {}, { signal } = {}) {
  const query = new URLSearchParams(params).toString();
  const url = `${API_BASE_URL}${path}${query ? `?${query}` : ""}`;

  const ctrl = new AbortController();
  let timedOut = false;
  const timer = setTimeout(() => { timedOut = true; ctrl.abort(); }, API_TIMEOUT_MS);
  const cancel = () => ctrl.abort();
  if (signal?.aborted) cancel();
  signal?.addEventListener("abort", cancel, { once: true });

  try {
    let res;
    try {
      res = await fetch(url, { signal: ctrl.signal, headers: { Accept: "application/json" } });
    } catch (e) {
      if (e.name === "AbortError") throw e;
      throw new ApiError("Não foi possível conectar à API.", 0); // falha de rede
    }
    const body = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new ApiError(body.erro || body.message || MESSAGES[res.status] || `Erro do servidor (${res.status}).`, res.status);
    }
    return body;
  } catch (e) {
    if (e.name === "AbortError" && timedOut) {
      throw new ApiError("A busca demorou demais. Refine os filtros e tente novamente.", 408);
    }
    throw e;
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener("abort", cancel);
  }
}
