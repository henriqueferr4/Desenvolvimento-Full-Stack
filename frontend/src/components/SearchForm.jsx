import { TABS, MODES, UFS, SITUACOES } from "../constants.js";

export default function SearchForm({ mode, setMode, values, onChange, onSubmit, onReset, loading, error }) {
  const show = (f) => MODES[mode].fields.includes(f);
  const bind = (name) => ({
    id: name,
    name,
    value: values[name],
    onChange: (e) => onChange(name, e.target.value),
  });

  return (
      <section className="card" aria-labelledby="busca-titulo">
        <h2 id="busca-titulo" className="sr-only">Busca</h2>

        <div className="tabs" role="tablist" aria-label="Tipo de busca">
          {TABS.map((t) => (
              <button
                  key={t.id}
                  type="button"
                  role="tab"
                  aria-selected={mode === t.id}
                  className={`tab${mode === t.id ? " is-active" : ""}`}
                  onClick={() => setMode(t.id)}
              >
                {t.label}
              </button>
          ))}
        </div>

        <form onSubmit={onSubmit} onReset={onReset} noValidate>
          <div className="grid">
            {show("nome") && (
                <div className={`field${mode === "nome" ? " field--wide" : ""}`}>
                  <label htmlFor="nome">Nome</label>
                  <input {...bind("nome")} type="text" maxLength={120} placeholder="Ex.: MARIA DA SILVA ou MARIA SILVA" autoComplete="off" />
                  {mode === "nome" && <small>Digite o nome completo ou apenas parte dele.</small>}
                </div>
            )}

            {show("cargo") && (
                <div className="field">
                  <label htmlFor="cargo">Cargo / profissão</label>
                  <input {...bind("cargo")} type="text" maxLength={120} placeholder="Ex.: PROFESSOR DO MAGISTERIO SUPERIOR" autoComplete="off" />
                </div>
            )}

            {show("uf") && (
                <div className="field">
                  <label htmlFor="uf">Estado (UF)</label>
                  <select {...bind("uf")}>
                    <option value="">Selecione…</option>
                    {UFS.map((u) => <option key={u} value={u}>{u}</option>)}
                  </select>
                  <small>A base de aposentados não informa UF: a busca por estado retorna apenas servidores ativos.</small>
                </div>
            )}

            {show("orgao") && (
                <div className="field">
                  <label htmlFor="orgao">Instituição / órgão</label>
                  <input {...bind("orgao")} type="text" maxLength={120} placeholder="Ex.: UNIVERSIDADE FEDERAL DO RIO GRANDE" autoComplete="off" />
                </div>
            )}

            {show("situacao") && (
                <div className="field">
                  <label htmlFor="situacao">Situação</label>
                  <select {...bind("situacao")}>
                    <option value="">Todas</option>
                    {SITUACOES.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                </div>
            )}

            <div className="field field--small">
              <label htmlFor="per_page">Resultados por página</label>
              <select {...bind("per_page")}>
                <option value="10">10</option>
                <option value="20">20</option>
                <option value="50">50</option>
              </select>
            </div>
          </div>

          {error && <p className="form-error" role="alert">{error}</p>}

          <div className="actions">
            <button type="submit" className="btn btn--primary" disabled={loading}>
              {loading ? "Buscando…" : "Buscar"}
            </button>
            <button type="reset" className="btn btn--ghost">Limpar</button>
          </div>
        </form>
      </section>
  );
}
