from dotenv import load_dotenv
from flask import Flask, jsonify, request
import os, psycopg

app = Flask(__name__)

load_dotenv()   #Pega o .env na pasta raiz do backend, ou acima (pasta raiz do projeto)

#Exemplo de configuração no .env:
#DB_URL=postgresql://postgres:minhasenha123@localhost:5432/meubanco
db_url = os.getenv("DB_URL")

valid_searches = ["nome", "cargo", "uf", "orgao"]   #Colunas válidas de pesquisa

@app.route("/api/servidores", methods=["GET"])
def getServidores():
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            # request.args.get
            pass

if __name__ == "__main__":
    app.run("0.0.0.0", 5000)