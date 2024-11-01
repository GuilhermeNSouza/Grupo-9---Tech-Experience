from flask import Flask, jsonify, request
import sqlite3
from flask_cors import CORS
import pandas as pd
from datetime import datetime, timedelta
import pywhatkit as kit
from apscheduler.schedulers.background import BackgroundScheduler
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
CORS(app)

DATABASE = 'database.db'

# Conjunto para armazenar produtos notificados
produtos_notificados = set()


# conectar ao banco de dados
def connection_database():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


# Função para enviar notificação via WhatsApp
def send_whatsapp_notification(produtos_proximos, phone_number="+5565999161641"):
    mensagem = "Aviso: Os seguintes produtos estão com validade próxima:\n"
    for produto in produtos_proximos:
        mensagem += f"- {produto['nome']} (Validade: {produto['dataValidade']})\n"
        
    agora = datetime.now()
    envio_hora = agora + timedelta(minutes=1)
    hora = envio_hora.hour
    minuto = envio_hora.minute

    try:
        kit.sendwhatmsg(phone_number, mensagem, hora, minuto)
        logging.info("Mensagem enviada com sucesso!")
    except Exception as e:
        logging.error(f"Erro ao enviar a mensagem: {e}")


# Função para verificar produtos próximos da validade e enviar notificações
def verificar_validade():
    logging.info("Verificando validade dos produtos...")
    global produtos_notificados
    conn = connection_database()
    cursor = conn.cursor()
    
    hoje = datetime.now().date()
    prazo = hoje + timedelta(days=7)

    logging.info(f"Verificando produtos com validade até: {prazo.isoformat()}")

    try:
        cursor.execute('''SELECT nome, dataValidade FROM produto WHERE dataValidade IS NOT NULL''')
        produtos = cursor.fetchall()
    except sqlite3.Error as e:
        logging.error(f"Erro ao executar a consulta: {e}")
        conn.close()
        return

    produtos_proximos = []
    for produto in produtos:
        nome = produto["nome"]
        validade_str = produto["dataValidade"]
        
        # Conversão de string para datetime
        try:
            # Supondo que dataValidade seja um timestamp em milissegundos
            validade_timestamp = int(validade_str)
            validade = datetime.fromtimestamp(validade_timestamp / 1000.0).date()
        except (ValueError, TypeError) as e:
            logging.error(f"Formato de validade inválido: {validade_str}. Erro: {e}")
            continue

        if validade <= prazo and nome not in produtos_notificados:
            produtos_proximos.append({"nome": nome, "dataValidade": validade})
            produtos_notificados.add(nome)

    conn.close()

    if produtos_proximos:
        send_whatsapp_notification(produtos_proximos)
        logging.info(f"Produtos próximos da validade: {produtos_proximos}")


# Rota da API para obter o relatório de vendas
@app.route('/api/vendas', methods=['GET'])
def obter_vendas():
    try:
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')

        if not data_inicio or not data_fim:
            return jsonify({'erro': 'Parâmetros data_inicio e data_fim são obrigatórios.'}), 400

        try:
            data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d')
            data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d')
        except ValueError:
            return jsonify({'erro': 'Formato de data inválido. Use AAAA-MM-DD.'}), 400

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
        logging.error(f"Erro na rota /api/vendas: {e}")
        return jsonify({'erro': str(e)}), 500


# Rota para obter notificações de validade
@app.route('/api/notificacoes-validade', methods=['GET'])
def notificacoes_validade():
    try:
        conn = connection_database()
        cursor = conn.cursor()
        
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
        logging.error(f"Erro: {e}")
        return jsonify({'erro': str(e)}), 500


# Função para prever demanda mensal
def prever_demanda_mensal_simples(dados_vendas, periodo_previsao):
    media_demanda = dados_vendas['quantidade'].tail(30).mean()
    total_previsto = max(0, round(media_demanda * periodo_previsao))
    return total_previsto


# Rota para prever demanda mensal
@app.route('/api/previsao_demanda_mensal', methods=['GET'])
def previsao_demanda_mensal():
    try:
        periodo_previsao = 30

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
        
        logging.info("Dados carregados do banco.")

        previsoes_mensais = {}

        for produto_nome, dados_produto in dados.groupby('produtoNome'):
            if len(dados_produto) < 10:
                previsoes_mensais[produto_nome] = {'erro': 'Dados insuficientes para previsão.'}
                continue

            total_previsto = prever_demanda_mensal_simples(dados_produto, periodo_previsao)

            previsoes_mensais[produto_nome] = {
                'produto': produto_nome,
                'total_previsto_proximo_mes': total_previsto
            }

        previsoes_ordenadas = sorted(previsoes_mensais.values(), key=lambda x: x.get('total_previsto_proximo_mes', 0), reverse=True)

        return jsonify(previsoes_ordenadas), 200
    except Exception as e:
        logging.error(f"Erro geral na rota /api/previsao_demanda_mensal: {e}")
        return jsonify({'erro': str(e)}), 500

# Início do agendador
scheduler = BackgroundScheduler()
scheduler.add_job(verificar_validade, 'interval', minutes=20)  # Verifica validade a cada 1 minuto
scheduler.start()

if __name__ == '__main__':
    app.run(debug=False, port=8080)
