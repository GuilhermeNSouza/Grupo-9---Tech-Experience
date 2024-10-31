from flask import Flask, jsonify, request
import sqlite3
from flask_cors import CORS
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)  # Habilita CORS para permitir requisições de origens diferentes

DATABASE = 'database.db'
# Função para conectar ao banco de dados
def connection_database():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection
# Rota da API para obter o relatório de vendas
@app.route('/api/vendas', methods=['GET'])
def obter_vendas():
    try:
        # Obtém os parâmetros de data e valor mínimo da requisição
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        valor_minimo = request.args.get('valor_minimo', type=float, default=0.0) 
        try:
            data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d')
            data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d')
            data_atual = datetime.now()
            
            if data_inicio_dt > data_atual or data_fim_dt > data_atual:
                return jsonify({'erro': 'Datas futuras não são permitidas.'}), 400
        except ValueError:
            return jsonify({'erro': 'Formato de data inválido. Utilize AAAA-MM-DD.'}), 400
        
        data_inicio_timestamp = int(data_inicio_dt.timestamp() * 1000)
        data_fim_timestamp = int(data_fim_dt.timestamp() * 1000)
        
        conn = connection_database()
        cursor = conn.cursor()
        

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
        
        vendas = []
        for row in resultado:
            vendas.append({
                'nome_produto': row['nome_produto'],
                'quantidade_estoque': row['quantidade_estoque'],
                'quantidade_vendida': row['quantidade_vendida'],
                'total_vendas': row['total_vendas']
            })
        
        conn.close()
        
        return jsonify(vendas), 200
    except Exception as e:
        print(f"Erro: {e}")
        return jsonify({'erro': str(e)}), 500
@app.route('/api/notificacoes-validade', methods=['GET'])
def notificacoes_validade():
    try:
        # Conecta ao banco de dados
        conn = connection_database()
        cursor = conn.cursor()
        
        # Consulta SQL para buscar todos os produtos ordenados pela data de validade
        query = '''
            SELECT
                nome,
                estoqueAtual,
                dataValidade
            FROM
                produto
            ORDER BY
                dataValidade ASC
        '''
        cursor.execute(query)
        produtos = cursor.fetchall()
        
        notificacoes = []
        for produto in produtos:
            notificacoes.append({
                'nome': produto['nome'],
                'quantidade': produto['estoqueAtual'],
                'validade': produto['dataValidade']
            })
        
        conn.close()
        
        return jsonify(notificacoes), 200
    except Exception as e:
        print(f"Erro: {e}")
        return jsonify({'erro': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8080)
