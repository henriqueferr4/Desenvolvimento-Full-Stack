import { Fragment } from "react";
import ServidorDetails from "./ServidorDetails.jsx";
import { show } from "../utils/format.js";

const COLS = 6;

export function ToggleAllButton({ expanded }) {
  return (
      <button type="button" className="btn btn--ghost btn--sm results__toggle-all" onClick={expanded.toggleAll} aria-pressed={expanded.allOpen}>
        {expanded.allOpen ? "Recolher todos" : "Expandir todos"}
      </button>
  );
}

export default function ResultsTable({ rows, expanded }) {
  const { open, keys, toggle } = expanded;

  return (
      <div className="table-wrap">
        <table>
          <thead>
          <tr>
            <th className="col-toggle"><span className="sr-only">Detalhes</span></th>
            <th>Nome</th><th>Cargo</th><th>UF</th><th>Órgão</th><th>Situação</th>
          </tr>
          </thead>
          <tbody>
          {rows.map((r, i) => {
            const k = keys[i];
            const isOpen = open.has(k);
            const detailId = `detalhe-${k}`;
            return (
                <Fragment key={k}>
                  <tr className={`row${i % 2 ? " is-alt" : ""}${isOpen ? " is-open" : ""}`} onClick={() => toggle(k)}>
                    <td className="col-toggle">
                      <button
                          type="button"
                          className="row-toggle"
                          aria-expanded={isOpen}
                          aria-controls={detailId}
                          aria-label={`${isOpen ? "Ocultar" : "Mostrar"} informações de ${show(r.nome)}`}
                          onClick={(e) => { e.stopPropagation(); toggle(k); }}
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                          <path d="m9 6 6 6-6 6" />
                        </svg>
                      </button>
                    </td>
                    <td>{show(r.nome)}</td>
                    <td>{show(r.cargo)}</td>
                    <td>{show(r.uf)}</td>
                    <td>{show(r.orgao)}</td>
                    <td><span className="tag">{show(r.situacao)}</span></td>
                  </tr>
                  {isOpen && (
                      <tr className="row-detail" id={detailId}>
                        <td colSpan={COLS}>
                          <ServidorDetails servidor={r} />
                        </td>
                      </tr>
                  )}
                </Fragment>
            );
          })}
          </tbody>
        </table>
      </div>
  );
}
