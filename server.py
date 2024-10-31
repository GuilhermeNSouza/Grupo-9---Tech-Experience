from sqlite3 import connect, Connection, Row, Cursor
from flask import Flask, jsonify, Response


# Banco de Dados
DATABASE: str = "database.db"


def connection_database() -> Connection:
    """
    Cria, configura e retorna uma conexão com o Banco de Dados
    :return: Conexão com o Banco de Dados
    """
    connection: Connection = connect(DATABASE)
    connection.row_factory = Row
    return connection


# Rotas
server: Flask = Flask(__name__)


@server.get("/api/products")
def get_products() -> tuple[Response, int]:
    """
    Rota GET "/api/products", para buscar todos os produtos do Banco de Dados
    :return: Lista de Produtos cadastrados no Banco de Dados
    """
    database: Connection = connection_database()
    cursor: Cursor = database.execute("SELECT * FROM produto")

    products: list[any] = cursor.fetchall()

    return jsonify([dict(product) for product in products]), 200


if __name__ == "__main__":
    server.run(debug=True, port=8080)
