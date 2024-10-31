from flask import Flask, jsonify, request
from datetime import datetime
import sqlite3
from flask_cors import CORS

app = Flask(__name__)
CORS(app) 

DATABASE = 'database.db'

# Database connection function
def connection_database():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection

# API route to get sales report with optional minimum value filter
@app.route('/api/vendas', methods=['GET'])
def obter_vendas():
    try:
        # Get date parameters from request
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        valor_minimo = request.args.get('valor_minimo', type=float, default=0.0)  # Default to 0 if not provided
        
        # Validate date format and check if dates are in the future
        try:
            data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d')
            data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d')
            data_atual = datetime.now()
            
            if data_inicio_dt > data_atual or data_fim_dt > data_atual:
                return jsonify({'erro': 'Datas futuras não são permitidas.'}), 400
        except ValueError:
            return jsonify({'erro': 'Formato de data inválido. Utilize AAAA-MM-DD.'}), 400
        
        # Convert dates to timestamps in milliseconds for SQL query
        data_inicio_timestamp = int(data_inicio_dt.timestamp() * 1000)
        data_fim_timestamp = int(data_fim_dt.timestamp() * 1000)
        
        # Connect to database
        conn = connection_database()
        cursor = conn.cursor()
        
        # SQL query to get sales report with date filter and minimum value filter
        query = '''
            SELECT
                p.nome AS nome_produto,
                IFNULL(p.estoqueAtual, 0) AS quantidade_estoque,
                SUM(vp.quantidadeProduto) AS quantidade_vendida,
                SUM(vp.quantidadeProduto * vp.precoVenda) AS total_vendas
            FROM
                Venda v
            JOIN
                VendaProduto vp ON v.id = vp.vendaId
            JOIN
                Produto p ON vp.produtoId = p.id
            WHERE
                v.dataVenda BETWEEN ? AND ?
            GROUP BY
                p.id, p.nome
            HAVING
                total_vendas >= ?
            ORDER BY
                quantidade_vendida DESC;
        '''
        cursor.execute(query, (data_inicio_timestamp, data_fim_timestamp, valor_minimo))
        resultado = cursor.fetchall()
        
        # Create list of results
        vendas = []
        for row in resultado:
            vendas.append({
                'nome_produto': row['nome_produto'],
                'quantidade_estoque': row['quantidade_estoque'],
                'quantidade_vendida': row['quantidade_vendida'],
                'total_vendas': row['total_vendas']
            })
        
        # Close connection
        conn.close()
        
        return jsonify(vendas), 200
    except Exception as e:
        print(f"Erro: {e}")
        return jsonify({'erro': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8080)
