import ResultsTable, { ToggleAllButton } from "./ResultsTable.jsx";
import { useExpanded } from "../hooks/useExpanded.js";
import ServidorDetails from "./ServidorDetails.jsx";
import { show } from "../utils/format.js";

export default function Results({ result, onPage }) {
  const rows = result.data?.data ?? [];
  const expanded = useExpanded(rows);

  if (result.status === "idle") {
    return (
      <section className="card results" aria-live="polite">
        <div className="empty">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" aria-hidden="true">
            <circle cx="11" cy="11" r="7" />
            <path d="m20 20-3.5-3.5" />
          </svg>
          <strong>Nenhuma busca realizada</strong>
          <p>Escolha um tipo de busca acima, preencha os critérios e clique em Buscar para ver os servidores.</p>
        </div>
      </section>
    );
  }

  const { status, data, message } = result;
  const total = data?.total ?? rows.length;
  const page = data?.page ?? 1;
  const pages = data?.pages ?? 1;

  return (
    <section className="card results" aria-live="polite">
      <div className="results__head">
        <h2>Resultados</h2>
        {status === "ok" && rows.length > 0 && (
          <span className="badge">{total} registro{total > 1 ? "s" : ""}</span>
        )}
        {status === "ok" && total > 1 && rows.length > 0 && <ToggleAllButton expanded={expanded} />}
      </div>

      {status === "loading" && <div className="status">Carregando resultados…</div>}
      {status === "error" && <div className="status status--error">{message}</div>}
      {status === "ok" && rows.length === 0 && (
        <div className="status">Nenhum servidor encontrado para esta busca.</div>
      )}

      {status === "ok" && total === 1 && rows.length === 1 && (
        <div className="detail">
          <h3>{show(rows[0].nome)}</h3>
          <ServidorDetails servidor={rows[0]} />
        </div>
      )}

      {status === "ok" && total > 1 && (
        <>
          <ResultsTable rows={rows} expanded={expanded} />

          {pages > 1 && (
            <nav className="pager" aria-label="Paginação">
              <button className="btn btn--ghost" disabled={page <= 1} onClick={() => onPage(1)}>« Primeira</button>
              <button className="btn btn--ghost" disabled={page <= 1} onClick={() => onPage(page - 1)}>‹ Anterior</button>
              <span className="pager__info">Página {page} de {pages}</span>
              <button className="btn btn--ghost" disabled={page >= pages} onClick={() => onPage(page + 1)}>Próxima ›</button>
              <button className="btn btn--ghost" disabled={page >= pages} onClick={() => onPage(pages)}>Última »</button>
            </nav>
          )}
        </>
      )}
    </section>
  );
}
