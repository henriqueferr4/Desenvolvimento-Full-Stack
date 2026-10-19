import { useState } from "react";

export const rowKey = (r, i) => String(r.id ?? `${r.nome}-${i}`);

// Controla quais linhas estão abertas. O estado fica atrelado à lista recebida:
// ao chegar uma nova página/busca, tudo começa fechado.
export function useExpanded(rows) {
  const [state, setState] = useState({ rows, open: new Set() });
  const open = state.rows === rows ? state.open : new Set();
  const keys = rows.map(rowKey);
  const allOpen = keys.length > 0 && keys.every((k) => open.has(k));

  const toggle = (k) => {
    const next = new Set(open);
    if (next.has(k)) next.delete(k);
    else next.add(k);
    setState({ rows, open: next });
  };
  const toggleAll = () => setState({ rows, open: allOpen ? new Set() : new Set(keys) });

  return { open, keys, allOpen, toggle, toggleAll };
}
