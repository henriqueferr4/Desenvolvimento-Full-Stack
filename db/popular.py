import argparse
import csv
import os
import re
import sys
import time
from datetime import datetime

import psycopg

try:  # opcional: lê o .env da raiz do projeto, se python-dotenv estiver instalado
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

DIR_BASE = os.path.dirname(os.path.abspath(__file__))

CABECALHO_APOSENTADOS = [
    "nome", "cpf", "matricula_servidor", "nome_orgao", "sigla_orgao",
    "codigo_orgao_superior", "cargo", "classe", "padrao", "referencia",
    "nivel", "tipo_aposentadoria", "fundamentacao_inatividade",
    "nome_diploma_legal", "Dt ocorrencia inatividade", "ocorrencia_ingresso",
    "Dt ingresso servico publico", "valor_rendimento_liquido"
]

CABECALHO_CARREIRAS = [
    "nome", "cpf", "codigo_carreira", "descricao_cargo_emprego",
    "uf_upag", "denominacao_orgao_atuacao", "mes_referencia", "valor_remuneracao"
]

ENCODING_BRUTO = "latin1"
BOM_LATIN1 = "ï»¿"  # BOM UTF-8 lido como latin1


def configuracao_banco():
    """Parâmetros de conexão a partir do ambiente. A senha é obrigatória."""
    senha = os.environ.get("POSTGRES_PASSWORD")
    if not senha:
        sys.exit("Defina POSTGRES_PASSWORD (no ambiente ou no .env) antes de executar.")
    return {
        "host": os.environ.get("DB_HOST", "localhost"),
        "port": os.environ.get("DB_PORT", "5432"),
        "dbname": os.environ.get("POSTGRES_DB", "executivo_federal_db"),
        "user": os.environ.get("POSTGRES_USER", "postgres"),
        "password": senha,
    }


def limpar_moeda(valor_str):
    if not valor_str:
        return 0.0
    try:
        return float(valor_str.strip().replace(".", "").replace(",", "."))
    except ValueError:
        return 0.0


def limpar_data(valor_str):
    if not valor_str:
        return None
    digitos = re.sub(r"\D", "", valor_str)
    if len(digitos) < 7 or len(digitos) > 8 or int(digitos) == 0:
        return None
    try:
        datetime.strptime(digitos.zfill(8), "%d%m%Y")
    except ValueError:
        return None
    return digitos


def precisa_converter(caminho_bruto, caminho_tratado, forcar=False):
    if forcar or not os.path.exists(caminho_tratado) or os.path.getsize(caminho_tratado) == 0:
        return True
    return os.path.getmtime(caminho_bruto) > os.path.getmtime(caminho_tratado)


def ler_linhas_csv(caminho):
    with open(caminho, "r", encoding=ENCODING_BRUTO, errors="replace", newline="") as f:
        sem_nulos = (linha.replace("\x00", "") for linha in f)
        for n, cols in enumerate(csv.reader(sem_nulos, delimiter=";")):
            cols = [c.strip() for c in cols]
            if n == 0 and cols:
                cols[0] = cols[0].removeprefix(BOM_LATIN1).removeprefix("﻿").strip()
            if any(cols):
                yield n, cols


def converter_aposentados(brutos, destino):
    with open(destino, "w", newline="", encoding="utf-8", buffering=1024 * 1024) as f_out:
        writer = csv.writer(f_out, delimiter=";")
        writer.writerow(CABECALHO_APOSENTADOS)
        for arquivo, caminho, qtd in brutos:
            print(f"-> Arquivo '{arquivo}' classificado como APOSENTADOS ({qtd} cols). Convertendo...")
            for _, cols in ler_linhas_csv(caminho):
                # ignora linhas incompletas, sem nome ou linha de cabeçalho
                if len(cols) < 18 or not cols[0] or cols[0].upper() == "NOME":
                    continue
                matricula = re.sub(r"\D", "", cols[2])
                writer.writerow([
                    cols[0], cols[1], int(matricula) if matricula else "", cols[3], cols[4],
                    cols[5], cols[6], cols[7], cols[8], cols[9], cols[10], cols[11], cols[12],
                    cols[13], limpar_data(cols[14]) or "", cols[15], limpar_data(cols[16]) or "",
                    limpar_moeda(cols[17])
                ])


def converter_carreiras(brutos, destino):
    with open(destino, "w", newline="", encoding="utf-8", buffering=1024 * 1024) as f_out:
        writer = csv.writer(f_out, delimiter=";")
        writer.writerow(CABECALHO_CARREIRAS)
        for arquivo, caminho, qtd in brutos:
            print(f"-> Arquivo '{arquivo}' classificado como CARREIRAS/CARGOS ({qtd} cols). Convertendo...")
            for n, cols in ler_linhas_csv(caminho):
                # ignora linhas incompletas, registros sem nome ou linha de cabeçalho
                if len(cols) < 8 or not cols[0] or (n == 0 and "CPF" in cols[1].upper()):
                    continue
                writer.writerow([
                    cols[0], cols[1], cols[2], cols[3], cols[4][:2].upper(),  # UF: 2 letras maiúsculas
                    cols[5], cols[6], limpar_moeda(cols[7])
                ])


def classificar_e_converter_arquivos(dir_bruto, dir_saida, forcar_conversao=False):
    os.makedirs(dir_saida, exist_ok=True)
    os.makedirs(dir_bruto, exist_ok=True)
    csv_apos = os.path.join(dir_saida, "aposentados_tratado.csv")
    csv_carr = os.path.join(dir_saida, "carreiras_tratado.csv")

    brutos_apos, brutos_carr = [], []
    for arquivo in sorted(os.listdir(dir_bruto)):
        if not arquivo.lower().endswith((".csv", ".txt")):
            continue
        caminho = os.path.join(dir_bruto, arquivo)
        with open(caminho, "rb") as f:
            primeira_linha = f.readline().decode(ENCODING_BRUTO, errors="replace")
        qtd = len(primeira_linha.split(";"))

        # aposentados: 18 colunas (mínimo para ser reconhecido: 15); carreiras: 8 (mínimo: 8)
        if qtd >= 15:
            brutos_apos.append((arquivo, caminho, qtd))
        elif 8 <= qtd < 15:
            brutos_carr.append((arquivo, caminho, qtd))
        else:
            print(f"-> [IGNORADO] '{arquivo}': {qtd} colunas, formato não reconhecido.")

    for brutos, destino, converter, rotulo in (
        (brutos_apos, csv_apos, converter_aposentados, "aposentados"),
        (brutos_carr, csv_carr, converter_carreiras, "carreiras"),
    ):
        if not brutos:
            continue
        if any(precisa_converter(c, destino, forcar_conversao) for _, c, _ in brutos):
            converter(brutos, destino)
        else:
            print(f"-> [CACHE] '{destino}' ({rotulo}) já está tratado e atualizado.")

    return (
        csv_apos if os.path.exists(csv_apos) else None,
        csv_carr if os.path.exists(csv_carr) else None,
    )


def copy_csv_rapido(cur, caminho_csv, sql_copy, limite=None):
    with open(caminho_csv, "r", encoding="utf-8", buffering=1024 * 1024, newline="") as f, \
            cur.copy(sql_copy) as copy:
        f.readline()  # descarta o cabeçalho (o COPY usa HEADER FALSE)
        if limite is None:
            while bloco := f.read(1024 * 1024):
                copy.write(bloco)
        else:
            for _ in range(limite):
                linha = f.readline()
                if not linha:
                    break
                copy.write(linha)


def ler_sql(nome):
    with open(os.path.join(DIR_BASE, "init", nome), encoding="utf-8") as f:
        return f.read()


def popular_banco(csv_apos, csv_carr, limite=None):
    if not csv_apos and not csv_carr:
        print("Nenhum arquivo CSV tratado disponível para popular o banco.")
        return

    inicio = time.time()
    # Tudo roda em UMA transação: se algo falhar, nada é alterado e a view continua no ar.
    with psycopg.connect(**configuracao_banco()) as conn, conn.cursor() as cur:
        cur.execute("SET LOCAL synchronous_commit = OFF")
        cur.execute("SET LOCAL maintenance_work_mem = '256MB'")

        print("-> Preparando tabelas (view e índices são recriados ao final)...")
        cur.execute("""
            DROP VIEW IF EXISTS servidores;

            DROP INDEX IF EXISTS idx_aposentados_nome_trgm;
            DROP INDEX IF EXISTS idx_aposentados_nome_exato;
            DROP INDEX IF EXISTS idx_aposentados_cargo_trgm;
            DROP INDEX IF EXISTS idx_aposentados_orgao_trgm;
            DROP INDEX IF EXISTS idx_carreiras_nome_trgm;
            DROP INDEX IF EXISTS idx_carreiras_nome_exato;
            DROP INDEX IF EXISTS idx_carreiras_cargo_trgm;
            DROP INDEX IF EXISTS idx_carreiras_orgao_trgm;
            DROP INDEX IF EXISTS idx_carreiras_uf;

            TRUNCATE TABLE aposentados, carreiras_cargos RESTART IDENTITY CASCADE;

            -- Compatibilidade com bancos criados por versões anteriores do script
            -- (datas viravam DATE e mes_referencia era VARCHAR(2)); no-op se já estiver certo.
            ALTER TABLE aposentados
                ALTER COLUMN "Dt ocorrencia inatividade" TYPE TEXT USING "Dt ocorrencia inatividade"::text,
                ALTER COLUMN "Dt ingresso servico publico" TYPE TEXT USING "Dt ingresso servico publico"::text;
            ALTER TABLE carreiras_cargos ALTER COLUMN mes_referencia TYPE TEXT;
        """)

        if csv_apos:
            t0 = time.time()
            copy_csv_rapido(cur, csv_apos, """
                COPY aposentados (
                    nome, cpf, matricula_servidor, nome_orgao, sigla_orgao,
                    codigo_orgao_superior, cargo, classe, padrao, referencia,
                    nivel, tipo_aposentadoria, fundamentacao_inatividade,
                    nome_diploma_legal, "Dt ocorrencia inatividade", ocorrencia_ingresso,
                    "Dt ingresso servico publico", valor_rendimento_liquido
                ) FROM STDIN WITH (FORMAT CSV, HEADER FALSE, DELIMITER ';', NULL '')
            """, limite=limite)
            print(f"[OK] Aposentados carregados via COPY em {time.time() - t0:.2f}s.")

        if csv_carr:
            t0 = time.time()
            copy_csv_rapido(cur, csv_carr, """
                COPY carreiras_cargos (
                    nome, cpf, codigo_carreira, descricao_cargo_emprego,
                    uf_upag, denominacao_orgao_atuacao, mes_referencia, valor_remuneracao
                ) FROM STDIN WITH (FORMAT CSV, HEADER FALSE, DELIMITER ';', NULL '')
            """, limite=limite)
            print(f"[OK] Carreiras/Cargos carregados via COPY em {time.time() - t0:.2f}s.")

        t0 = time.time()
        print("-> Recriando view servidores e construindo índices...")
        cur.execute(ler_sql("02_view.sql"))
        cur.execute(ler_sql("03_indexes.sql"))
        cur.execute("ANALYZE aposentados")
        cur.execute("ANALYZE carreiras_cargos")
        print(f"[OK] Índices e view criados em {time.time() - t0:.2f}s.")
    # saindo do `with` sem exceção, a transação é confirmada
    print(f"\n[SUCESSO] Operação completa finalizada em {time.time() - inicio:.2f}s")


def confirmar():
    if not sys.stdin.isatty():
        sys.exit("Execução não interativa: use --sim para confirmar a substituição dos dados.")
    resp = input("Isto APAGA todos os dados de 'aposentados' e 'carreiras_cargos' e recarrega do zero. Continuar? [s/N] ")
    return resp.strip().lower() in ("s", "sim", "y", "yes")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--limite", type=int, default=None, help="Limite de linhas por tabela (ex: 50)")
    parser.add_argument("--forcar-conversao", action="store_true", help="Força recriar os CSVs tratados")
    parser.add_argument("--sim", action="store_true", help="Não pede confirmação antes de substituir os dados")
    args = parser.parse_args()

    csv_apos, csv_carr = classificar_e_converter_arquivos(
        os.path.join(DIR_BASE, "dados_brutos"),
        os.path.join(DIR_BASE, "dados_tratados"),
        forcar_conversao=args.forcar_conversao,
    )
    if (csv_apos or csv_carr) and (args.sim or confirmar()):
        popular_banco(csv_apos, csv_carr, limite=args.limite)
    elif csv_apos or csv_carr:
        print("Operação cancelada.")
    else:
        print("Nenhum arquivo CSV tratado disponível para popular o banco.")
