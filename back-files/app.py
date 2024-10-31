from flask import Flask, jsonify, request
import sqlite3
from flask_cors import CORS
from datetime import datetime
import pandas as pd

app = Flask(__name__)
CORS(app)  # Cors e para aceitar outras portas para chamadas ainda esta aberta pois esta em modo teste mas como e um sistema de um mercado iria apenas aceitar requisiçoes da rede do mercado 

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
        # Obtém os parâmetros de data da requisição
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        # Verifica se os parâmetros de data estão presentes
        if not data_inicio or not data_fim:
            return jsonify({'erro': 'Parâmetros data_inicio e data_fim são obrigatórios.'}), 400

        # Tenta converter as datas para o formato correto
        try:
            data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d')
            data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d')
        except ValueError:
            return jsonify({'erro': 'Formato de data inválido. Use AAAA-MM-DD.'}), 400

        # Converte as datas para timestamp
        data_inicio_timestamp = int(data_inicio_dt.timestamp() * 1000)
        data_fim_timestamp = int(data_fim_dt.timestamp() * 1000)

        # Conexão ao banco de dados e execução da query
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
            ORDER BY
                quantidade_vendida DESC;
        '''
        cursor.execute(query, (data_inicio_timestamp, data_fim_timestamp))
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
        print(f"Erro na rota /api/vendas: {e}")
        return jsonify({'erro': str(e)}), 500

@app.route('/api/notificacoes-validade', methods=['GET'])
def notificacoes_validade():
    try:
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
def prever_demanda_mensal_simples(dados_vendas, periodo_previsao):
    media_demanda = dados_vendas['quantidade'].tail(30).mean()
    
    # Multiplica a média pelo período de previsão (30 dias) para obter a previsão mensal
    total_previsto = max(0, round(media_demanda * periodo_previsao))  # Garante que seja no mínimo zero
    return total_previsto

@app.route('/api/previsao_demanda_mensal', methods=['GET'])
def previsao_demanda_mensal():
    try:
        # Define o período de previsão para 1 mês (30 dias)
        periodo_previsao = 30

        # Conecta ao banco e busca os dados históricos de vendas de todos os produtos
        conn = connection_database()
        query = '''
            SELECT p.nome AS produtoNome, v.dataVenda AS data, vp.quantidadeProduto AS quantidade
            FROM VendaProduto vp
            JOIN Venda v ON vp.vendaId = v.id
            JOIN Produto p ON vp.produtoId = p.id
            ORDER BY p.nome, v.dataVenda
        '''
        dados = pd.read_sql_query(query, conn)
        conn.close()
        
        # Verifica se os dados foram carregados corretamente
        print("Dados carregados do banco:", dados.head())

        # Dicionário para armazenar previsões por produto
        previsoes_mensais = {}

        # Processar previsões por produto
        for produto_nome, dados_produto in dados.groupby('produtoNome'):
            if len(dados_produto) < 10:
                previsoes_mensais[produto_nome] = {'erro': 'Dados insuficientes para previsão.'}
                continue

            # Calcula a previsão agregada para o próximo mês usando média simples
            total_previsto = prever_demanda_mensal_simples(dados_produto, periodo_previsao)
                
            # Armazena o total previsto para o produto
            previsoes_mensais[produto_nome] = {
                'produto': produto_nome,
                'total_previsto_proximo_mes': total_previsto
            }

        # Transforma o dicionário de previsões em uma lista e ordena pela quantidade total prevista
        previsoes_ordenadas = sorted(previsoes_mensais.values(), key=lambda x: x.get('total_previsto_proximo_mes', 0), reverse=True)

        return jsonify(previsoes_ordenadas), 200
    except Exception as e:
        print(f"Erro geral na rota /api/previsao_demanda_mensal: {e}")
        return jsonify({'erro': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=False, port=8080)
