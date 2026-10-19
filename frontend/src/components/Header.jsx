export default function Header() {
  return (
    <>
      <header className="topbar">
        <div className="container topbar__inner">
          <a className="brand" href="/" aria-label="GovData">
            <img src="/favicon.svg" width="34" height="34" alt="" />
            <span>Gov<strong>Data</strong></span>
          </a>
          <span className="topbar__tag">Portal de acesso a informações de Servidores Federais</span>
        </div>
      </header>
      <section className="hero">
        <div className="container">
          <h1>Consulte servidores ativos e aposentados</h1>
          <p>Busque por nome, cargo, UF ou órgão com dados abertos do dados.gov.br.</p>
        </div>
      </section>
    </>
  );
}
