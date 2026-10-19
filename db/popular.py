import os
import re
import csv
import argparse
import psycopg2
from psycopg2.extras import execute_values

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
    if not valor_str: return 0.0
    try: return float(valor_str.strip().replace(".", "").replace(",", "."))
    except ValueError: return 0.0

def limpar_data(valor_str):
    if not valor_str: return None
    digitos = re.sub(r"\D", "", valor_str)
    if len(digitos) < 7 or len(digitos) > 8 or int(digitos) == 0: return None
    return digitos

def classificar_e_converter_arquivos(dir_bruto, dir_saida):
    os.makedirs(dir_saida, exist_ok=True)
    csv_apos = os.path.join(dir_saida, "aposentados_tratado.csv")
    csv_carr = os.path.join(dir_saida, "carreiras_tratado.csv")
    
    encontrou_algo = False

    if not os.path.exists(dir_bruto):
        os.makedirs(dir_bruto)
        return None, None

    for arquivo in os.listdir(dir_bruto):
        if not arquivo.lower().endswith(('.csv', '.txt')):
            continue
            
        caminho_bruto = os.path.join(dir_bruto, arquivo)
        encontrou_algo = True
        
        with open(caminho_bruto, 'rb') as f:
            primeira_linha = f.readline().decode('latin1', errors='replace')
            qtd_colunas = len(primeira_linha.split(';'))

        if qtd_colunas >= 15:
            print(f"-> Arquivo '{arquivo}' classificado como APOSENTADOS ({qtd_colunas} colunas). Convertendo...")
            with open(caminho_bruto, "rb") as f_in, open(csv_apos, "w", newline="", encoding="utf-8") as f_out:
                writer = csv.writer(f_out, delimiter=";")
                writer.writerow(CABECALHO_APOSENTADOS)
                for linha in f_in:
                    texto = linha.decode("latin1", errors="replace").replace("\x00", "").strip()
                    if not texto: continue
                    cols = [c.strip() for c in texto.split(";")]
                    if len(cols) < 18 or cols[0].upper() == "NOME": continue
                    
                    matricula = re.sub(r"\D", "", cols[2])
                    writer.writerow([
                        cols[0], cols[1], int(matricula) if matricula else None, cols[3], cols[4],
                        cols[5], cols[6], cols[7], cols[8], cols[9], cols[10], cols[11], cols[12],
                        cols[13], limpar_data(cols[14]), cols[15], limpar_data(cols[16]),
                        limpar_moeda(cols[17])
                    ])
        elif 7 <= qtd_colunas < 15:
            print(f"-> Arquivo '{arquivo}' classificado como CARREIRAS/CARGOS ({qtd_colunas} colunas). Convertendo...")
            with open(caminho_bruto, "rb") as f_in, open(csv_carr, "w", newline="", encoding="utf-8") as f_out:
                writer = csv.writer(f_out, delimiter=";")
                writer.writerow(CABECALHO_CARREIRAS)
                for i, linha in enumerate(f_in):
                    texto = linha.decode("latin1", errors="replace").replace("\x00", "").strip()
                    if not texto: continue
                    cols = [c.strip() for c in texto.split(";")]
                    if len(cols) < 8 or (i == 0 and "CPF" in cols[1].upper()): continue
                    
                    writer.writerow([
                        cols[0][:60], cols[1][:14], cols[2][:10], cols[3][:60], cols[4][:2],
                        cols[5][:60], cols[6][:2], limpar_moeda(cols[7])
                    ])

    if not encontrou_algo:
        print(f"Nenhum arquivo .csv ou .txt encontrado em '{dir_bruto}'.")
        return None, None

    return (csv_apos if os.path.exists(csv_apos) else None, 
            csv_carr if os.path.exists(csv_carr) else None)

def executar_script_professor(cur, conn):
    print("-> Aplicando script para converter datas (TEXT -> DATE)...")
    cur.execute("""
        ALTER TABLE aposentados ALTER COLUMN "Dt ocorrencia inatividade" TYPE DATE 
        USING to_date(lpad("Dt ocorrencia inatividade"::text, 8, '0'), 'DDMMYYYY');
        ALTER TABLE aposentados ALTER COLUMN "Dt ingresso servico publico" TYPE DATE 
        USING to_date(lpad("Dt ingresso servico publico"::text, 8, '0'), 'DDMMYYYY');
    """)
    conn.commit()

def popular_banco(csv_apos, csv_carr, limite=None):
    if not csv_apos and not csv_carr:
        return

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    try:
        #Para evitar o erro "cannot alter type of a column used by a view or rule", derruba a view temporariamente.
        cur.execute("DROP VIEW IF EXISTS vw_servidores;")
        
        cur.execute("TRUNCATE TABLE aposentados, carreiras_cargos RESTART IDENTITY CASCADE;")
        cur.execute("""
            ALTER TABLE aposentados 
            ALTER COLUMN "Dt ocorrencia inatividade" TYPE TEXT USING "Dt ocorrencia inatividade"::text,
            ALTER COLUMN "Dt ingresso servico publico" TYPE TEXT USING "Dt ingresso servico publico"::text;
        """)
        conn.commit()

        if csv_apos:
            with open(csv_apos, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter=";")
                lote = []
                total = 0
                sql = "INSERT INTO aposentados (nome, cpf, matricula_servidor, nome_orgao, sigla_orgao, codigo_orgao_superior, cargo, classe, padrao, referencia, nivel, tipo_aposentadoria, fundamentacao_inatividade, nome_diploma_legal, \"Dt ocorrencia inatividade\", ocorrencia_ingresso, \"Dt ingresso servico publico\", valor_rendimento_liquido) VALUES %s"
                for r in reader:
                    lote.append((
                        r["nome"], r["cpf"], int(r["matricula_servidor"]) if r["matricula_servidor"] else None,
                        r["nome_orgao"], r["sigla_orgao"], r["codigo_orgao_superior"], r["cargo"], r["classe"],
                        r["padrao"], r["referencia"], r["nivel"], r["tipo_aposentadoria"], r["fundamentacao_inatividade"],
                        r["nome_diploma_legal"] or None, r["Dt ocorrencia inatividade"] or None, r["ocorrencia_ingresso"],
                        r["Dt ingresso servico publico"] or None, float(r["valor_rendimento_liquido"])
                    ))
                    if limite and (total + len(lote)) >= limite: break
                    if len(lote) >= 5000:
                        execute_values(cur, sql, lote)
                        total += len(lote)
                        lote.clear()
                if lote: execute_values(cur, sql, lote)
                print(f"[OK] Aposentados inseridos.")

        executar_script_professor(cur, conn)

        if csv_carr:
            with open(csv_carr, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter=";")
                lote = []
                total = 0
                sql = "INSERT INTO carreiras_cargos (nome, cpf, codigo_carreira, descricao_cargo_emprego, uf_upag, denominacao_orgao_atuacao, mes_referencia, valor_remuneracao) VALUES %s"
                for r in reader:
                    lote.append((r["nome"], r["cpf"], r["codigo_carreira"], r["descricao_cargo_emprego"], r["uf_upag"], r["denominacao_orgao_atuacao"], r["mes_referencia"], float(r["valor_remuneracao"])))
                    if limite and (total + len(lote)) >= limite: break
                    if len(lote) >= 5000:
                        execute_values(cur, sql, lote)
                        total += len(lote)
                        lote.clear()
                if lote: execute_values(cur, sql, lote)
                print(f"[OK] Carreiras inseridas.")

        print("-> Recriando a View vw_servidores e otimizando índices...")
        cur.execute("""
            CREATE OR REPLACE VIEW vw_servidores AS
            SELECT 
                id, nome, cpf, cargo, NULL::VARCHAR(2) AS uf, nome_orgao AS orgao,
                sigla_orgao, 'APOSENTADO' AS situacao_vinculo,
                TO_CHAR("Dt ocorrencia inatividade", 'DD/MM/YYYY') AS data_inatividade,
                TO_CHAR("Dt ingresso servico publico", 'DD/MM/YYYY') AS data_ingresso_servico_publico,
                valor_rendimento_liquido AS remuneracao
            FROM aposentados
            UNION ALL
            SELECT 
                id, nome, cpf, descricao_cargo_emprego AS cargo, uf_upag AS uf,
                denominacao_orgao_atuacao AS orgao, NULL::VARCHAR(20) AS sigla_orgao,
                'ATIVO' AS situacao_vinculo, NULL::TEXT AS data_inatividade,
                NULL::TEXT AS data_ingresso_servico_publico, valor_remuneracao AS remuneracao
            FROM carreiras_cargos;
            
            ANALYZE aposentados; 
            ANALYZE carreiras_cargos;
        """)
        conn.commit()
        print("[SUCESSO] Operação concluída!")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limite", type=int, default=None)
    args = parser.parse_args()

    diretorio_bruto = "db/dados_brutos"
    diretorio_tratado = "db/dados_tratados"
    
    csv_apos, csv_carr = classificar_e_converter_arquivos(diretorio_bruto, diretorio_tratado)
    popular_banco(csv_apos, csv_carr, limite=args.limite)