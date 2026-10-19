// Gera mock/servidores.json com servidores fictícios para testar o frontend.
// Uso: npm run mock:gerar  (ou: node mock/gerar.js [quantidade])
// A semente é fixa: o mesmo comando sempre gera o mesmo arquivo.
import { writeFileSync } from "node:fs";

const QUANTIDADE = Number(process.argv[2]) || 300;

// PRNG determinístico (mulberry32)
let seed = 20261019;
const rand = () => {
  seed = (seed + 0x6d2b79f5) | 0;
  let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
  t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
};
const pick = (arr) => arr[Math.floor(rand() * arr.length)];
const int = (min, max) => min + Math.floor(rand() * (max - min + 1));

const FEMININOS = ["MARIA", "ANA", "FRANCISCA", "ANTONIA", "ADRIANA", "JULIANA", "MARCIA", "FERNANDA", "PATRICIA", "ALINE",
  "CAMILA", "BEATRIZ", "LETICIA", "LUCIANA", "HELENA"];
const MASCULINOS = ["JOSE", "JOAO", "ANTONIO", "FRANCISCO", "CARLOS", "PAULO", "PEDRO", "LUCAS", "LUIZ", "MARCOS",
  "RAFAEL", "HENRIQUE", "RODRIGO", "GABRIEL", "BRUNO", "EDUARDO"];
const MEIOS_F = ["", "", "", "APARECIDA", "CRISTINA", "HELENA", "DE FATIMA", "LUIZA", "EDUARDA"];
const MEIOS_M = ["", "", "", "CARLOS", "LUIZ", "EDUARDO", "AUGUSTO", "HENRIQUE", "PAULO"];
// sobrenomes já com a preposição usual
const SOBRENOMES = ["SILVA", "DA SILVA", "SANTOS", "DOS SANTOS", "OLIVEIRA", "DE OLIVEIRA", "SOUZA", "DE SOUZA",
  "RODRIGUES", "FERREIRA", "ALVES", "PEREIRA", "LIMA", "GOMES", "COSTA", "DA COSTA", "RIBEIRO", "MARTINS",
  "CARVALHO", "DE CARVALHO", "ALMEIDA", "DE ALMEIDA", "LOPES", "SOARES", "FERNANDES", "VIEIRA", "BARBOSA",
  "ROCHA", "DA ROCHA", "DIAS", "NASCIMENTO", "DO NASCIMENTO", "ANDRADE", "DE ANDRADE", "MOREIRA", "NUNES",
  "MENDES", "FREITAS", "DE FREITAS", "CARDOSO", "TEIXEIRA"];

const UNIVERSIDADE = ["PROFESSOR DO MAGISTERIO SUPERIOR", "PROFESSOR DO MAGISTERIO SUPERIOR", "ASSISTENTE EM ADMINISTRACAO",
  "TECNICO EM ASSUNTOS EDUCACIONAIS", "TECNICO DE LABORATORIO AREA", "MEDICO-AREA", "ENFERMEIRO-AREA", "BIBLIOTECARIO-DOCUMENTALISTA"];
const INSTITUTO = ["PROFESSOR ENS BASICO TECN TECNOLOGICO", "ASSISTENTE EM ADMINISTRACAO", "TECNICO EM ASSUNTOS EDUCACIONAIS", "PEDAGOGO-AREA"];

// órgãos locais (com UF fixa) e nacionais (qualquer UF)
const ORGAOS = [
  ["UNIVERSIDADE FEDERAL DO RIO GRANDE", "RS", UNIVERSIDADE],
  ["UNIVERSIDADE FEDERAL DO RIO GRANDE DO SUL", "RS", UNIVERSIDADE],
  ["UNIVERSIDADE FEDERAL DE PELOTAS", "RS", UNIVERSIDADE],
  ["UNIVERSIDADE FEDERAL DE SANTA CATARINA", "SC", UNIVERSIDADE],
  ["UNIVERSIDADE FEDERAL DO PARANA", "PR", UNIVERSIDADE],
  ["UNIVERSIDADE FEDERAL DE MINAS GERAIS", "MG", UNIVERSIDADE],
  ["UNIVERSIDADE FEDERAL DO RIO DE JANEIRO", "RJ", UNIVERSIDADE],
  ["UNIVERSIDADE DE BRASILIA", "DF", UNIVERSIDADE],
  ["UNIVERSIDADE FEDERAL DA BAHIA", "BA", UNIVERSIDADE],
  ["UNIVERSIDADE FEDERAL DE PERNAMBUCO", "PE", UNIVERSIDADE],
  ["UNIVERSIDADE FEDERAL DO CEARA", "CE", UNIVERSIDADE],
  ["UNIVERSIDADE FEDERAL DO PARA", "PA", UNIVERSIDADE],
  ["UNIVERSIDADE FEDERAL DO AMAZONAS", "AM", UNIVERSIDADE],
  ["INSTITUTO FEDERAL DO RIO GRANDE DO SUL", "RS", INSTITUTO],
  ["INSTITUTO FEDERAL DE SAO PAULO", "SP", INSTITUTO],
  ["INSTITUTO FEDERAL DE GOIAS", "GO", INSTITUTO],
  ["INSTITUTO NACIONAL DO SEGURO SOCIAL", null, ["ANALISTA DO SEGURO SOCIAL", "TECNICO DO SEGURO SOCIAL", "PERITO MEDICO FEDERAL"]],
  ["SECRETARIA ESPECIAL DA RECEITA FEDERAL DO BRASIL", null, ["AUDITOR-FISCAL DA RECEITA FEDERAL DO BRASIL", "ANALISTA-TRIBUTARIO DA RECEITA FEDERAL DO BRASIL"]],
  ["DEPARTAMENTO DE POLICIA FEDERAL", null, ["AGENTE DE POLICIA FEDERAL", "DELEGADO DE POLICIA FEDERAL", "ESCRIVAO DE POLICIA FEDERAL", "PAPILOSCOPISTA POLICIAL FEDERAL"]],
  ["MINISTERIO DA SAUDE", null, ["MEDICO", "ENFERMEIRO", "AGENTE ADMINISTRATIVO", "SANITARISTA"]],
  ["FUNDACAO INSTITUTO BRASILEIRO DE GEOGRAFIA E ESTATISTICA", null, ["TECNOLOGISTA EM INFORMACOES GEOGRAFICAS E ESTATISTICAS", "ANALISTA DE PLANEJAMENTO, GESTAO E INFRAESTRUTURA"]],
];
const UFS = "AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split(" ");

const sem = (s) => s.replace(/^(DA|DE|DO|DOS) /, "");

const nome = () => {
  const fem = rand() < 0.5;
  const primeiro = pick(fem ? FEMININOS : MASCULINOS);
  let meio = pick(fem ? MEIOS_F : MEIOS_M);
  if (meio === primeiro) meio = "";
  const partes = [primeiro, meio];
  const ultimo = pick(SOBRENOMES);
  if (rand() < 0.6) {
    let sobrenome = sem(pick(SOBRENOMES));
    while (sobrenome === sem(ultimo)) sobrenome = sem(pick(SOBRENOMES));
    partes.push(sobrenome);
  }
  partes.push(ultimo);
  return partes.filter(Boolean).join(" ");
};

const pad = (n, len) => String(n).padStart(len, "0");

const servidor = (id, fixo = {}) => {
  const [orgao, ufOrgao, cargos] = pick(ORGAOS);
  const ano = int(1985, 2024);
  const situacao = ano < 1998 && rand() < 0.6 ? "APOSENTADO" : rand() < 0.1 ? "APOSENTADO" : "ATIVO";
  return {
    id,
    nome: nome(),
    cpf: `***.${pad(int(0, 999), 3)}.${pad(int(0, 999), 3)}-**`,
    matricula: pad(int(1000000, 9999999), 7),
    cargo: pick(cargos),
    orgao,
    uf: ufOrgao ?? pick(UFS),
    situacao,
    jornada: pick(["40 HORAS SEMANAIS", "40 HORAS SEMANAIS", "DEDICACAO EXCLUSIVA", "20 HORAS SEMANAIS"]),
    data_ingresso: `${ano}-${pad(int(1, 12), 2)}-${pad(int(1, 28), 2)}`,
    ...fixo,
  };
};

const lista = Array.from({ length: QUANTIDADE }, (_, i) => servidor(i + 1));

// casos fixos para testar cenários específicos
lista.push(
  servidor(lista.length + 1, { nome: "MARIA DA SILVA" }),
  servidor(lista.length + 2, { nome: "MARIA DA SILVA", situacao: "APOSENTADO" }),
  servidor(lista.length + 3, { nome: "TEOBALDO QUINTINO ZAMBELLI" }), // resultado único → tela de detalhe
);

const destino = new URL("./servidores.json", import.meta.url);
writeFileSync(destino, JSON.stringify(lista, null, 2) + "\n");
console.log(`${lista.length} servidores gravados em ${destino.pathname}`);
