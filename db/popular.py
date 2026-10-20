import os
import re
import csv
import time
import argparse
from datetime import datetime
from io import StringIO
import psycopg2

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "5432"),
    "dbname": os.environ.get("POSTGRES_DB", "executivo_federal_db"),
    "user": os.environ.get("POSTGRES_USER", "postgres"),
    "password": os.environ.get("POSTGRES_PASSWORD", "postgres_password"),
}

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

def classificar_e_converter_arquivos(dir_bruto, dir_saida, forcar_conversao=False):
    os.makedirs(dir_saida, exist_ok=True)
    csv_apos = os.path.join(dir_saida, "aposentados_tratado.csv")
    csv_carr = os.path.join(dir_saida, "carreiras_tratado.csv")

    if not os.path.exists(dir_bruto):
        os.makedirs(dir_bruto, exist_ok=True)

    arquivos_brutos = [
        f for f in sorted(os.listdir(dir_bruto))
        if f.lower().endswith((".csv", ".txt"))
    ]

    brutos_apos = []
    brutos_carr = []

    for arquivo in arquivos_brutos:
        caminho_bruto = os.path.join(dir_bruto, arquivo)

        with open(caminho_bruto, "rb") as f:
            primeira_linha = f.readline().decode("latin1", errors="replace")
            qtd_colunas = len(primeira_linha.split(";"))

        if qtd_colunas >= 15:
            brutos_apos.append((arquivo, caminho_bruto, qtd_colunas))
        elif 7 <= qtd_colunas < 15:
            brutos_carr.append((arquivo, caminho_bruto, qtd_colunas))

    if brutos_apos:
        if not any(precisa_converter(caminho, csv_apos, forcar_conversao) for _, caminho, _ in brutos_apos):
            print(f"-> [CACHE] '{csv_apos}' já está tratado e atualizado.")
        else:
            with open(csv_apos, "w", newline="", encoding="utf-8", buffering=1024*1024) as f_out:
                writer = csv.writer(f_out, delimiter=";")
                writer.writerow(CABECALHO_APOSENTADOS)
                for arquivo, caminho_bruto, qtd_colunas in brutos_apos:
                    print(f"-> Arquivo '{arquivo}' classificado como APOSENTADOS ({qtd_colunas} cols). Convertendo...")
                    with open(caminho_bruto, "rb") as f_in:
                        for linha in f_in:
                            texto = linha.decode("latin1", errors="replace").replace("\x00", "").strip()
                            if not texto:
                                continue
                            cols = [c.strip() for c in texto.split(";")]
                            #Ignora linhas incompletas, sem nome ou linha de cabeçalho
                            if len(cols) < 18 or not cols[0] or cols[0].upper() == "NOME":
                                continue

                            matricula = re.sub(r"\D", "", cols[2])
                            writer.writerow([
                                cols[0], cols[1], int(matricula) if matricula else "", cols[3], cols[4],
                                cols[5], cols[6], cols[7], cols[8], cols[9], cols[10], cols[11], cols[12],
                                cols[13], limpar_data(cols[14]) or "", cols[15], limpar_data(cols[16]) or "",
                                limpar_moeda(cols[17])
                            ])

    if brutos_carr:
        if not any(precisa_converter(caminho, csv_carr, forcar_conversao) for _, caminho, _ in brutos_carr):
            print(f"-> [CACHE] '{csv_carr}' já está tratado e atualizado.")
        else:
            with open(csv_carr, "w", newline="", encoding="utf-8", buffering=1024*1024) as f_out:
                writer = csv.writer(f_out, delimiter=";")
                writer.writerow(CABECALHO_CARREIRAS)
                for arquivo, caminho_bruto, qtd_colunas in brutos_carr:
                    print(f"-> Arquivo '{arquivo}' classificado como CARREIRAS/CARGOS ({qtd_colunas} cols). Convertendo...")
                    with open(caminho_bruto, "rb") as f_in:
                        for i, linha in enumerate(f_in):
                            texto = linha.decode("latin1", errors="replace").replace("\x00", "").strip()
                            if not texto:
                                continue
                            cols = [c.strip() for c in texto.split(";")]
                            #Ignora linhas incompletas, registros sem nome ou linha de cabeçalho
                            if len(cols) < 8 or not cols[0] or (i == 0 and "CPF" in cols[1].upper()):
                                continue

                            writer.writerow([
                                cols[0], cols[1], cols[2], cols[3], cols[4][:2],
                                cols[5], cols[6][:2], limpar_moeda(cols[7])
                            ])

    return (
        csv_apos if os.path.exists(csv_apos) else None,
        csv_carr if os.path.exists(csv_carr) else None
    )

def copy_csv_rapido(cur, caminho_csv, sql_copy, limite=None):
    with open(caminho_csv, "r", encoding="utf-8", buffering=1024*1024) as f:
        if limite is None:
            cur.copy_expert(sql_copy, f)
        else:
            buffer_limitado = StringIO()
            cabecalho = f.readline()
            buffer_limitado.write(cabecalho)
            for _ in range(limite):
                linha = f.readline()
                if not linha:
                    break
                buffer_limitado.write(linha)
            buffer_limitado.seek(0)
            cur.copy_expert(sql_copy, buffer_limitado)

def executar_script_professor(cur):
    print("-> Aplicando script para converter datas (TEXT -> DATE)...")
    cur.execute("""
        ALTER TABLE aposentados ALTER COLUMN "Dt ocorrencia inatividade" TYPE DATE 
        USING to_date(lpad("Dt ocorrencia inatividade"::text, 8, '0'), 'DDMMYYYY');
        ALTER TABLE aposentados ALTER COLUMN "Dt ingresso servico publico" TYPE DATE 
        USING to_date(lpad("Dt ingresso servico publico"::text, 8, '0'), 'DDMMYYYY');
    """)

def popular_banco(csv_apos, csv_carr, limite=None):
    if not csv_apos and not csv_carr:
        print("Nenhum arquivo CSV tratado disponível para popular o banco.")
        return

    inicio = time.time()
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    try:
        cur.execute("SET synchronous_commit = OFF;")
        cur.execute("SET maintenance_work_mem = '256MB';")

        print("-> Preparando tabelas e suspendendo view...")
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

            ALTER TABLE aposentados 
            ALTER COLUMN "Dt ocorrencia inatividade" TYPE TEXT USING "Dt ocorrencia inatividade"::text,
            ALTER COLUMN "Dt ingresso servico publico" TYPE TEXT USING "Dt ingresso servico publico"::text;
        """)
        conn.commit()

        if csv_apos:
            t0 = time.time()
            sql_copy_apos = """
                COPY aposentados (
                    nome, cpf, matricula_servidor, nome_orgao, sigla_orgao,
                    codigo_orgao_superior, cargo, classe, padrao, referencia,
                    nivel, tipo_aposentadoria, fundamentacao_inatividade,
                    nome_diploma_legal, "Dt ocorrencia inatividade", ocorrencia_ingresso,
                    "Dt ingresso servico publico", valor_rendimento_liquido
                ) FROM STDIN WITH (FORMAT CSV, HEADER TRUE, DELIMITER ';', NULL '');
            """
            copy_csv_rapido(cur, csv_apos, sql_copy_apos, limite=limite)
            print(f"[OK] Aposentados carregados via COPY em {time.time() - t0:.2f}s.")

        executar_script_professor(cur)
        conn.commit()

        if csv_carr:
            t0 = time.time()
            sql_copy_carr = """
                COPY carreiras_cargos (
                    nome, cpf, codigo_carreira, descricao_cargo_emprego,
                    uf_upag, denominacao_orgao_atuacao, mes_referencia, valor_remuneracao
                ) FROM STDIN WITH (FORMAT CSV, HEADER TRUE, DELIMITER ';', NULL '');
            """
            copy_csv_rapido(cur, csv_carr, sql_copy_carr, limite=limite)
            conn.commit()
            print(f"[OK] Carreiras/Cargos carregados via COPY em {time.time() - t0:.2f}s.")

        t0 = time.time()
        print("-> Recriando View servidores e construindo índices...")
        cur.execute("""
            CREATE OR REPLACE VIEW servidores AS
            SELECT 
                id, 'A-' || id::TEXT AS chave, nome, cpf, cargo, NULL::TEXT AS uf, nome_orgao AS orgao,
                sigla_orgao, 'APOSENTADO' AS situacao_vinculo,
                TO_CHAR("Dt ocorrencia inatividade", 'DD/MM/YYYY') AS data_inatividade,
                TO_CHAR("Dt ingresso servico publico", 'DD/MM/YYYY') AS data_ingresso_servico_publico,
                valor_rendimento_liquido AS remuneracao
            FROM aposentados
            UNION ALL
            SELECT 
                id, 'C-' || id::TEXT AS chave, nome, cpf, descricao_cargo_emprego AS cargo, uf_upag::TEXT AS uf,
                denominacao_orgao_atuacao AS orgao, NULL::TEXT AS sigla_orgao,
                'ATIVO' AS situacao_vinculo, NULL::TEXT AS data_inatividade,
                NULL::TEXT AS data_ingresso_servico_publico, valor_remuneracao AS remuneracao
            FROM carreiras_cargos;

            CREATE INDEX idx_aposentados_nome_trgm ON aposentados USING gin (nome gin_trgm_ops);
            CREATE INDEX idx_aposentados_nome_exato ON aposentados (UPPER(nome));
            CREATE INDEX idx_aposentados_cargo_trgm ON aposentados USING gin (cargo gin_trgm_ops);
            CREATE INDEX idx_aposentados_orgao_trgm ON aposentados USING gin (nome_orgao gin_trgm_ops);

            CREATE INDEX idx_carreiras_nome_trgm ON carreiras_cargos USING gin (nome gin_trgm_ops);
            CREATE INDEX idx_carreiras_nome_exato ON carreiras_cargos (UPPER(nome));
            CREATE INDEX idx_carreiras_cargo_trgm ON carreiras_cargos USING gin (descricao_cargo_emprego gin_trgm_ops);
            CREATE INDEX idx_carreiras_orgao_trgm ON carreiras_cargos USING gin (denominacao_orgao_atuacao gin_trgm_ops);
            CREATE INDEX idx_carreiras_uf ON carreiras_cargos (UPPER(uf_upag));

            ANALYZE aposentados; 
            ANALYZE carreiras_cargos;
        """)
        conn.commit()
        print(f"[OK] Índices e View criados em {time.time() - t0:.2f}s.")
        print(f"\n[SUCESSO] Operação completa finalizada em {time.time() - inicio:.2f}s")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limite", type=int, default=None, help="Limite de linhas por tabela (ex: 50)")
    parser.add_argument("--forcar-conversao", action="store_true", help="Força recriar os CSVs tratados")
    args = parser.parse_args()

    diretorio_base = os.path.dirname(os.path.abspath(__file__))
    diretorio_bruto = os.path.join(diretorio_base, "dados_brutos")
    diretorio_tratado = os.path.join(diretorio_base, "dados_tratados")

    csv_apos, csv_carr = classificar_e_converter_arquivos(
        diretorio_bruto, diretorio_tratado, forcar_conversao=args.forcar_conversao
    )
    popular_banco(csv_apos, csv_carr, limite=args.limite)
