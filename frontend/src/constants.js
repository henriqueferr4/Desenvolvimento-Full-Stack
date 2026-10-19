export const UFS = "AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split(" ");

export const SITUACOES = [
  { value: "ATIVO", label: "Ativo" },
  { value: "APOSENTADO", label: "Aposentado" },
];

export const TABS = [
  { id: "nome", label: "Nome" },
  { id: "cargo", label: "Cargo" },
  { id: "uf", label: "Estado (UF)" },
  { id: "orgao", label: "Órgão" },
  { id: "avancada", label: "Busca avançada" },
];

// campos usados por aba e mínimo de critérios preenchidos
export const MODES = {
  nome: { fields: ["nome"], min: 1 },
  cargo: { fields: ["cargo"], min: 1 },
  uf: { fields: ["uf"], min: 1 },
  orgao: { fields: ["orgao"], min: 1 },
  avancada: { fields: ["nome", "cargo", "uf", "orgao", "situacao"], min: 1 },
};

export const INITIAL_VALUES = {
  nome: "", cargo: "", uf: "", orgao: "", situacao: "", per_page: "20",
};
