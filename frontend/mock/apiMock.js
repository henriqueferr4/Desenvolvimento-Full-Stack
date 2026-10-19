// Plugin do Vite que simula a API Flask durante `npm run dev:mock`.
// Segue o contrato descrito em src/services/api.js; não entra no build.
//
// Cenários especiais: digite no campo Nome (ou Cargo/Órgão)
//   #400 #404 #429 #500 #502 #504 → responde com esse status
//   #lento                         → demora 20 s (testa o timeout do frontend)
import { readFileSync } from "node:fs";

const UFS = new Set("AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split(" "));
const FILTROS = ["nome", "similar", "cargo", "uf", "orgao", "situacao"];
const SITUACOES = new Set(["ATIVO", "APOSENTADO"]);

// maiúsculas, sem acentos e com espaços normalizados
const norm = (s) => String(s ?? "").normalize("NFD").replace(/\p{Diacritic}/gu, "").replace(/\s+/g, " ").trim().toUpperCase();

// LIKE do SQL: % é curinga, o restante precisa casar por inteiro
const like = (padrao) => {
  const re = norm(padrao).split("%").map((p) => p.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join(".*");
  return new RegExp(`^${re}$`);
};

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function send(res, status, body) {
  res.statusCode = status;
  res.setHeader("Content-Type", "application/json; charset=utf-8");
  res.end(JSON.stringify(body));
}

function inteiro(valor, padrao, min, max, nome) {
  if (valor === null || valor === "") return padrao;
  const n = Number(valor);
  if (!Number.isInteger(n) || n < min || n > max) throw new Error(`'${nome}' deve ser um número entre ${min} e ${max}.`);
  return n;
}

function buscar(dados, q) {
  const f = Object.fromEntries(FILTROS.map((k) => [k, norm(q.get(k))]).filter(([, v]) => v));
  if (!Object.keys(f).length) throw new Error("Informe ao menos um critério de busca.");
  if (f.uf && !UFS.has(f.uf)) throw new Error("UF inválida.");
  if (f.situacao && !SITUACOES.has(f.situacao)) throw new Error("Situação inválida.");

  const page = inteiro(q.get("page"), 1, 1, 100000, "page");
  const perPage = inteiro(q.get("per_page"), 20, 1, 50, "per_page");
  const limit = f.similar ? inteiro(q.get("limit"), 100, 1, 100, "limit") : Infinity;
  const similar = f.similar && like(f.similar);

  let rows = dados.filter((s) =>
    (!f.nome || norm(s.nome) === f.nome) &&
    (!similar || similar.test(norm(s.nome))) &&
    (!f.cargo || norm(s.cargo).includes(f.cargo)) &&
    (!f.uf || s.uf === f.uf) &&
    (!f.orgao || norm(s.orgao).includes(f.orgao)) &&
    (!f.situacao || norm(s.situacao) === f.situacao),
  );
  // nomes idênticos ao digitado (sem os %) aparecem primeiro
  const exato = f.similar && f.similar.replace(/%+/g, " ").trim();
  const rank = (s) => (exato && norm(s.nome) === exato ? 0 : 1);
  rows = rows.sort((a, b) => rank(a) - rank(b) || a.nome.localeCompare(b.nome)).slice(0, limit);

  const total = rows.length;
  return {
    total,
    page,
    per_page: perPage,
    pages: Math.max(1, Math.ceil(total / perPage)),
    data: rows.slice((page - 1) * perPage, page * perPage),
  };
}

export default function apiMock({ delay = 400 } = {}) {
  const arquivo = new URL("./servidores.json", import.meta.url);

  return {
    name: "govdata-api-mock",
    apply: "serve",
    configureServer(server) {
      server.config.logger.info("  ➜  API mock ativa em /api (mock/servidores.json)");

      server.middlewares.use("/api", async (req, res) => {
        const url = new URL(req.url, "http://localhost");
        await sleep(delay); // deixa o "Carregando…" visível

        if (req.method !== "GET") return send(res, 405, { erro: "Método não permitido." });
        if (url.pathname === "/health") return send(res, 200, { status: "ok", mock: true });
        if (url.pathname !== "/servidores") return send(res, 404, { erro: "Recurso não encontrado." });

        // o frontend envia o Nome como %...%: ignora os curingas para achar o comando
        const especial = FILTROS.map((k) => (url.searchParams.get(k) ?? "").replace(/%/g, "").trim()).find((v) => v.startsWith("#"));
        if (especial) {
          const cmd = especial.slice(1).toLowerCase();
          if (cmd === "lento") {
            await sleep(20000);
            return send(res, 504, { erro: "Tempo de busca excedido no servidor." });
          }
          // corpo vazio: o frontend exibe a própria mensagem para o status
          if (/^\d{3}$/.test(cmd)) return send(res, Number(cmd), {});
        }

        try {
          // relido a cada requisição: editar o JSON não exige reiniciar o Vite
          const dados = JSON.parse(readFileSync(arquivo, "utf8"));
          send(res, 200, buscar(dados, url.searchParams));
        } catch (e) {
          send(res, e instanceof SyntaxError ? 500 : 400, { erro: e.message });
        }
      });
    },
  };
}
