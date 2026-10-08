from flask import Flask, jsonify, request
import psycopg

app = Flask(__name__)

@app.route("/api/servidores", methods=["GET"])
def getServidores():
    pass

if __name__ == "__main__":
    app.run("0.0.0.0", 8000)