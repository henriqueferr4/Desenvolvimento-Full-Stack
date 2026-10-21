import logging
import os
import re

import psycopg
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from psycopg.rows import dict_row

load_dotenv()

DB_URL = os.getenv("DB_URL") or os.getenv("DATABASE_URL")
TABLE_NAME = "servidores"
STATEMENT_TIMEOUT_MS = int(os.getenv("STATEMENT_TIMEOUT_MS", "10000"))

UFS = frozenset("AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split())
SITUACOES = frozenset({"ATIVO", "APOSENTADO"})
FILTROS = ("nome", "similar", "cargo", "uf", "orgao", "situacao")
PARAMS_ACEITOS = frozenset(FILTROS) | {"page", "per_page", "limit"}
MAX_TEXTO = 120

COLUNAS = (
    "chave, id, nome, cpf, cargo, uf, orgao, sigla_orgao, "
    "situacao_vinculo AS situacao, data_inatividade, data_ingresso_servico_publico, remuneracao"
)

app = Flask(__name__)
app.json.ensure_ascii = False
app.json.sort_keys = False
log = logging.getLogger(__name__)


class ErroDeBusca(Exception):

    def __init__(self, erros):
        super().__init__(erros[0])
        self.erros = erros


def resposta_erro(status, *mensagens):
    return jsonify({"erro": mensagens[0], "erros": list(mensagens)}), status


def normaliza(valor):
    #Remove espaços repetidos e das pontas.
    return re.sub(r"\s+", " ", valor).strip()


def escapa_like(texto):
    #Escapa \\, % e _ para o texto ser tratado literalmente num LIKE.
    return texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def inteiro(valor, padrao, minimo, maximo, nome, erros):
    if valor is None or valor == "":
        return padrao
    try:
        n = int(valor)
    except ValueError:
        n = None
    if n is None or not minimo <= n <= maximo:
        erros.append(f"'{nome}' deve ser um número inteiro entre {minimo} e {maximo}.")
        return padrao
    return n


def monta_busca(args):
    erros = []

    desconhecidos = sorted(set(args) - PARAMS_ACEITOS)
    if desconhecidos:
        erros.append(f"Parâmetro de busca inválido: {', '.join(desconhecidos)}.")

    valores = {}
    for campo in FILTROS:
        bruto = args.get(campo, "")
        v = normaliza(bruto)
        if not v:
            continue  # parâmetro vazio = filtro não informado
        if len(v) > MAX_TEXTO:
            erros.append(f"'{campo}' deve ter no máximo {MAX_TEXTO} caracteres.")
            continue
        valores[campo] = v

    if not valores and not erros:
        erros.append("Informe ao menos um critério de busca.")

    if "uf" in valores:
        valores["uf"] = valores["uf"].upper()
        if valores["uf"] not in UFS:
            erros.append("UF inválida.")
    if "situacao" in valores:
        valores["situacao"] = valores["situacao"].upper()
        if valores["situacao"] not in SITUACOES:
            erros.append("Situação inválida.")
    if "similar" in valores and not valores["similar"].replace("%", "").replace("_", "").strip():
        erros.append("Digite um nome válido.")

    page = inteiro(args.get("page"), 1, 1, 100000, "page", erros)
    per_page = inteiro(args.get("per_page"), 20, 1, 50, "per_page", erros)
    limit = inteiro(args.get("limit"), 100, 1, 100, "limit", erros)

    if erros:
        raise ErroDeBusca(erros)

    condicoes, params = [], []
    if "nome" in valores:
        condicoes.append("UPPER(nome) = UPPER(%s)")
        params.append(valores["nome"])
    if "similar" in valores:
        # "%" vem do frontend como curinga; "_" e "\" são tratados como texto comum
        padrao = valores["similar"].replace("\\", "\\\\").replace("_", "\\_")
        condicoes.append("nome ILIKE %s")
        params.append(padrao)
    if "cargo" in valores:
        condicoes.append("cargo ILIKE %s")
        params.append(f"%{escapa_like(valores['cargo'])}%")
    if "orgao" in valores:
        condicoes.append("orgao ILIKE %s")
        params.append(f"%{escapa_like(valores['orgao'])}%")
    if "uf" in valores:
        condicoes.append("uf = %s")
        params.append(valores["uf"])
    if "situacao" in valores:
        condicoes.append("situacao_vinculo = %s")
        params.append(valores["situacao"])

    # nomes idênticos ao digitado (sem os %) aparecem primeiro
    exato = None
    if "similar" in valores:
        exato = normaliza(valores["similar"].replace("%", " ")).upper()

    return {
        "where": " AND ".join(condicoes),
        "params": params,
        "exato": exato,
        "page": page,
        "per_page": per_page,
        # o teto de resultados só vale para a busca por similaridade
        "limit": limit if "similar" in valores else None,
    }


def conectar():
    if not DB_URL:
        raise RuntimeError("Variável DB_URL não configurada.")
    return psycopg.connect(
        DB_URL,
        row_factory=dict_row,
        connect_timeout=5,
        options=f"-c statement_timeout={STATEMENT_TIMEOUT_MS}",
    )


@app.get("/api/servidores")
def listar_servidores():
    try:
        b = monta_busca(request.args)
    except ErroDeBusca as e:
        return resposta_erro(400, *e.erros)

    where = f"WHERE {b['where']}" if b["where"] else ""
    page, per_page, limit = b["page"], b["per_page"], b["limit"]
    offset = (page - 1) * per_page

    try:
        with conectar() as conn, conn.cursor() as cur:
            # total real (limitado ao teto, quando houver)
            teto = f"LIMIT {limit}" if limit else ""
            cur.execute(f"SELECT COUNT(*) AS n FROM (SELECT 1 FROM {TABLE_NAME} {where} {teto}) t", b["params"])
            total = cur.fetchone()["n"]

            linhas = []
            tamanho = min(per_page, max(total - offset, 0))
            if tamanho > 0:
                ordem = "nome, chave"
                params = list(b["params"])
                if b["exato"]:
                    ordem = "CASE WHEN UPPER(nome) = %s THEN 0 ELSE 1 END, nome, chave"
                    params.append(b["exato"])
                cur.execute(
                    f"SELECT {COLUNAS} FROM {TABLE_NAME} {where} ORDER BY {ordem} LIMIT %s OFFSET %s",
                    [*params, tamanho, offset],
                )
                linhas = cur.fetchall()
    except psycopg.errors.QueryCanceled:
        return resposta_erro(504, "Tempo de busca excedido no servidor.")
    except (psycopg.OperationalError, RuntimeError):
        log.exception("Banco de dados indisponível")
        return resposta_erro(503, "Banco de dados indisponível no momento.")
    except psycopg.Error:
        log.exception("Erro na consulta")
        return resposta_erro(500, "Erro interno do servidor.")

    return jsonify(
        {
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": max(1, -(-total // per_page)),
            "data": linhas,
        }
    )


@app.get("/api/health")
def health():
    try:
        with conectar() as conn:
            conn.execute("SELECT 1")
    except (psycopg.Error, RuntimeError):
        log.exception("Health check falhou")
        return resposta_erro(503, "Banco de dados indisponível.")
    return jsonify({"status": "ok"})


# Erros fora das rotas também respondem em JSON (o frontend lê "erro")
@app.errorhandler(404)
def nao_encontrado(_):
    return resposta_erro(404, "Recurso não encontrado.")


@app.errorhandler(405)
def metodo_nao_permitido(_):
    return resposta_erro(405, "Método não permitido.")


@app.errorhandler(500)
def erro_interno(_):
    return resposta_erro(500, "Erro interno do servidor.")


if __name__ == "__main__":
    app.run("0.0.0.0", 5000)
