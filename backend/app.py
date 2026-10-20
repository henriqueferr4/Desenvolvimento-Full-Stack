from dotenv import load_dotenv
from flask import Flask, jsonify, request
import os, psycopg, re
import psycopg.sql as sql

app = Flask(__name__)

load_dotenv()   #Pega o .env na pasta raiz do backend, ou acima (pasta raiz do projeto)

#Exemplo de configuração no .env:
#DB_URL=postgresql://postgres:minhasenha123@localhost:5432/meubanco
db_url = os.getenv("DB_URL")

pattern = r'[\w\s]*|%?[\w\s]*%?[\w\s]*%?'

@app.route("/api/servidores", methods=["GET"])
def getServidores():
    result = {"errors": []}
    query = "SELECT * FROM "
    table_name = "servidores"           #Se o nome for diferente no banco, mude aqui
    query += table_name
    queryparams = []
    first = True

    if request.args == []:
        result["errors"].append("Nenhum argumento de pesquisa")
    else:
        for arg in request.args:
            if first == True:
                query += " WHERE"
                first = False
            else: 
                query += " AND"
            match arg:
                case "nome":
                    try:
                        nome = request.args.get(arg, type=str)
                        if re.fullmatch(pattern, nome):
                            query += " nome = %s"
                            queryparams.append(nome)
                        else:
                            raise ValueError("Valor inválido inserido")
                    except ValueError:
                        result["errors"].append("Nome inválido")
                case "cargo":
                    try:
                        cargo = request.args.get(arg, type=str)
                        if re.fullmatch(pattern, cargo):
                            query += " cargo = %s"
                            queryparams.append(cargo)
                        else:
                            raise ValueError("Valor inválido inserido")
                    except ValueError:
                        result["errors"].append("Cargo inválido")
                case "uf": 
                    try:
                        uf = request.args.get(arg, type=str)
                        if re.fullmatch(pattern, uf):
                            query += " uf = %s"
                            queryparams.append(uf)
                        else:
                            raise ValueError("Valor inválido inserido")
                    except ValueError:
                        result["errors"].append("UF inválida")
                case "orgao": 
                    try:
                        orgao = request.args.get(arg, type=str)
                        if re.fullmatch(pattern, orgao):
                            query += " orgao = %s"
                            queryparams.append(orgao)
                        else:
                            raise ValueError("Valor inválido inserido")
                    except ValueError:
                        result["errors"].append("Órgão inválido")
                case "similar":
                    try:
                        similar = request.args.get(arg, type=str)
                        if re.fullmatch(pattern, similar):
                            query += " nome LIKE %s"
                            queryparams.append(similar)
                        else:
                            raise ValueError("Valor inválido inserido")
                    except ValueError:
                        result["errors"].append("Valor inválido")
                case _:
                    result["errors"].append("Parâmetro de busca inválido")

    if result["errors"] == []:
        query += " LIMIT 100;"
        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(query, queryparams)
                rows = cur.fetchall()
                result["rows"] = rows

    return jsonify(result)

if __name__ == "__main__":
    app.run("0.0.0.0", 5000)