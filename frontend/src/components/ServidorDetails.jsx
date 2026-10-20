import { show } from "../utils/format.js";

// identificadores internos: não interessam a quem consulta
const OCULTOS = new Set(["id", "chave"]);

// lista os campos retornados pela API para um servidor
export default function ServidorDetails({ servidor, className = "" }) {
  return (
      <dl className={`fields ${className}`}>
        {Object.entries(servidor).filter(([k]) => !OCULTOS.has(k)).map(([k, v]) => (
            <div key={k} className="fields__item">
              <dt>{k.replace(/_/g, " ")}</dt>
              <dd>{show(v)}</dd>
            </div>
        ))}
      </dl>
  );
}
