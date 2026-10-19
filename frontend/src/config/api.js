// URL base da API. Vazio = mesma origem (/api), atendida pelo proxy do Vite
// em desenvolvimento e pelo nginx em produção. Para uma API em outro domínio,
// defina VITE_API_URL=https://api.exemplo.gov.br no .env antes do build.
export const API_BASE_URL = (import.meta.env.VITE_API_URL ?? "").replace(/\/+$/, "");
export const API_TIMEOUT_MS = Number(import.meta.env.VITE_API_TIMEOUT_MS) || 15000;
