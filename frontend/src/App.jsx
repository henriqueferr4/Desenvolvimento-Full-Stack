import { useRef, useState } from "react";
import Header from "./components/Header.jsx";
import SearchForm from "./components/SearchForm.jsx";
import Results from "./components/Results.jsx";
import { MODES, INITIAL_VALUES } from "./constants.js";
import { fetchServidores } from "./services/api.js";

const clean = (v) => v.replace(/\s+/g, " ").trim();

// "maria silva" -> "%MARIA%SILVA%": acha o nome completo ou partes dele, em ordem.
// % e _ digitados pelo usuário são descartados (curingas do LIKE).
const namePattern = (nome) => `%${nome.replace(/[%_]/g, " ").trim().split(/\s+/).join("%").toUpperCase()}%`;

function buildParams(mode, values) {
  const cfg = MODES[mode];
  const p = {};
  let filled = 0;
  for (const f of cfg.fields) {
    const v = clean(values[f] ?? "");
    if (!v) continue;
    filled++;
    p[f] = v;
  }
  if (filled < cfg.min) {
    return { error: mode === "avancada" ? "Na busca avançada, preencha pelo menos um critério." : "Preencha o campo de busca." };
  }
  if (p.nome !== undefined) {
    if (!p.nome.replace(/[%_]/g, "").trim()) return { error: "Digite um nome válido." };
    p.similar = namePattern(p.nome);
    delete p.nome;
  }
  p.per_page = values.per_page;
  return { params: p };
}

export default function App() {
  const [mode, setMode] = useState("nome");
  const [values, setValues] = useState(INITIAL_VALUES);
  const [formError, setFormError] = useState("");
  const [result, setResult] = useState({ status: "idle" });
  const lastParams = useRef(null);

  const run = async (params, page = 1) => {
    setResult((r) => ({ ...r, status: "loading" }));
    try {
      const data = await fetchServidores(params, page);
      setResult({ status: "ok", data });
    } catch (e) {
      setResult({ status: "error", message: e.message });
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const { params, error } = buildParams(mode, values);
    setFormError(error || "");
    if (error) return;
    lastParams.current = params;
    run(params, 1);
  };

  const handleReset = (e) => {
    e.preventDefault();
    setValues(INITIAL_VALUES);
    setFormError("");
    setResult({ status: "idle" });
    lastParams.current = null;
  };

  const changeMode = (m) => { setMode(m); setFormError(""); };

  return (
    <>
      <Header />
      <main className="container">
        <SearchForm
          mode={mode}
          setMode={changeMode}
          values={values}
          onChange={(name, v) => setValues((s) => ({ ...s, [name]: v }))}
          onSubmit={handleSubmit}
          onReset={handleReset}
          loading={result.status === "loading"}
          error={formError}
        />
        <Results result={result} onPage={(p) => lastParams.current && run(lastParams.current, p)} />
      </main>
      <footer className="footer">
        <div className="container footer__inner">
          <div className="footer__about">
            <span>© {new Date().getFullYear()} GovData</span>
            <small>Projeto acadêmico desenvolvido no âmbito da disciplina de Sistemas para Internet II</small>
          </div>
          <span>
            Dados: <a href="https://dados.gov.br" target="_blank" rel="noreferrer">Portal Brasileiro de Dados Abertos</a>
          </span>
        </div>
      </footer>
    </>
  );
}