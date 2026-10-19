import { show } from "../utils/format.js";

// lista todos os campos retornados pela API para um servidor
export default function ServidorDetails({ servidor, className = "" }) {
  return (
    <dl className={`fields ${className}`}>
      {Object.entries(servidor).map(([k, v]) => (
        <div key={k} className="fields__item">
          <dt>{k.replace(/_/g, " ")}</dt>
          <dd>{show(v)}</dd>
        </div>
      ))}
    </dl>
  );
}
