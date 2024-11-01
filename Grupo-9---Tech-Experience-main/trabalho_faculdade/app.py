from flask import Flask, jsonify, request
import sqlite3
from flask_cors import CORS
from datetime import datetime, timedelta
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading
import time
import logging
import pywhatkit as kit
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
CORS(app)  # Cors e para aceitar outras portas para chamadas ainda esta aberta pois esta em modo teste mas como e um sistema de um mercado iria apenas aceitar requisiçoes da rede do mercado 

produtos_notificados = set()


# SIM EU SEI QUE A CHAVE DA API E PARA ESTAR EM OUTRO LUGAR E CRIPTOGRAFADA MAS NAO TENHO TEMPO PARA FAZER ISSO AGORA
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
app.config['SECRET_KEY'] = '3216bde14e948d5fff6bdc94871d8b9716b0dcf01ce5f1fd'
DATABASE = 'database.db'
# Função para conectar ao banco de dados
def connection_database():
    connection = sqlite3.connect(DATABASE, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    return connection



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
    media_demanda = dados_vendas['quantidade'].mean()
    total_previsto = max(0, round(media_demanda * periodo_previsao))
    return total_previsto

@app.route('/api/previsao_demanda_mensal', methods=['GET'])
def previsao_demanda_mensal():
    try:
        # Recebe as datas de início e fim da requisição
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')

        # Verifica se as datas foram enviadas
        if not data_inicio or not data_fim:
            return jsonify({'erro': 'Parâmetros data_inicio e data_fim são obrigatórios.'}), 400

        # Converte as datas para timestamps em milissegundos
        try:
            data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d')
            data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d')
            data_inicio_timestamp = int(data_inicio_dt.timestamp() * 1000)
            data_fim_timestamp = int(data_fim_dt.timestamp() * 1000)
        except ValueError:
            return jsonify({'erro': 'Formato de data inválido. Use AAAA-MM-DD.'}), 400

        # Calcula o número de dias no intervalo
        dias_no_periodo = (data_fim_dt - data_inicio_dt).days + 1  # +1 para incluir o último dia
        dias_proximo_mes = 30  # Supondo que estamos projetando para um mês de 30 dias

        # Conecta ao banco e busca os dados históricos de vendas no intervalo fornecido
        conn = connection_database()
        query = '''
            SELECT p.nome AS produtoNome, vp.quantidadeProduto AS quantidade
            FROM VendaProduto vp
            JOIN Venda v ON vp.vendaId = v.id
            JOIN Produto p ON vp.produtoId = p.id
            WHERE v.dataVenda BETWEEN ? AND ?
        '''
        dados = pd.read_sql_query(query, conn, params=[data_inicio_timestamp, data_fim_timestamp])
        conn.close()

        # Verifica se há dados no intervalo especificado
        if dados.empty:
            return jsonify({'mensagem': 'Nenhum dado de vendas encontrado no intervalo especificado.'}), 200

        # Calcula a média diária de vendas para cada produto e projeta para o próximo mês
        previsao_demanda = (
            dados.groupby('produtoNome')['quantidade']
            .sum()  # Soma a quantidade total vendida no período
            .apply(lambda total_vendido: (total_vendido / dias_no_periodo) * dias_proximo_mes)  # Projeção mensal
            .reset_index()
        )
        previsao_demanda.columns = ['produto', 'total_previsto_proximo_mes']

        # Converte o DataFrame em uma lista de dicionários para a resposta JSON, arredondando os valores
        previsao = previsao_demanda.to_dict(orient='records')
        for item in previsao:
            item['total_previsto_proximo_mes'] = round(item['total_previsto_proximo_mes'])

        return jsonify(previsao), 200
    except Exception as e:
        print(f"Erro na rota /api/previsao_demanda_mensal: {e}")
        return jsonify({'erro': str(e)}), 500


@app.route('/api/previsao_demanda_sazonal', methods=['GET'])
def previsao_demanda_sazonal():
    try:
        # Recebe as datas de início e fim da requisição
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')

        # Verifica se as datas foram enviadas
        if not data_inicio or not data_fim:
            return jsonify({'erro': 'Parâmetros data_inicio e data_fim são obrigatórios.'}), 400

        # Converte as datas para timestamps em milissegundos
        try:
            data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d')
            data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d')
            data_inicio_timestamp = int(data_inicio_dt.timestamp() * 1000)
            data_fim_timestamp = int(data_fim_dt.timestamp() * 1000)
        except ValueError:
            return jsonify({'erro': 'Formato de data inválido. Use AAAA-MM-DD.'}), 400

        # Calcula o número de dias no intervalo
        dias_no_periodo = (data_fim_dt - data_inicio_dt).days + 1  # +1 para incluir o último dia
        dias_proximo_mes = 30  # Supondo que estamos projetando para um mês de 30 dias

        # Conecta ao banco e busca os dados históricos de vendas no intervalo fornecido
        conn = connection_database()
        query = '''
            SELECT p.nome AS produtoNome, vp.quantidadeProduto AS quantidade
            FROM VendaProduto vp
            JOIN Venda v ON vp.vendaId = v.id
            JOIN Produto p ON vp.produtoId = p.id
            WHERE v.dataVenda BETWEEN ? AND ?
        '''
        dados = pd.read_sql_query(query, conn, params=[data_inicio_timestamp, data_fim_timestamp])
        conn.close()

        # Verifica se há dados no intervalo especificado
        if dados.empty:
            return jsonify({'mensagem': 'Nenhum dado de vendas encontrado no intervalo especificado.'}), 200

        # Calcula a média diária de vendas para cada produto e projeta para o próximo mês
        previsao_demanda = (
            dados.groupby('produtoNome')['quantidade']
            .sum()  # Soma a quantidade total vendida no período
            .apply(lambda total_vendido: (total_vendido / dias_no_periodo) * dias_proximo_mes)  # Projeção mensal
            .reset_index()
        )
        previsao_demanda.columns = ['produto', 'media_mensal_prevista']

        # Converte o DataFrame em uma lista de dicionários para a resposta JSON, arredondando os valores
        previsao = previsao_demanda.to_dict(orient='records')
        for item in previsao:
            item['media_mensal_prevista'] = round(item['media_mensal_prevista'])

        return jsonify(previsao), 200
    except Exception as e:
        print(f"Erro na rota /api/previsao_demanda_sazonal: {e}")
        return jsonify({'erro': str(e)}), 500











@app.route('/api/alertas-validade-estoque', methods=['GET'])
def alertas_validade_estoque():
    try:
        conn = connection_database()
        cursor = conn.cursor()
        query = '''
            SELECT nome, estoqueAtual, dataValidade
            FROM produto
            WHERE dataValidade <= ? OR dataValidade BETWEEN ? AND ?
            ORDER BY dataValidade ASC
        '''
        hoje = datetime.now()
        proximidade_validade = hoje + timedelta(days=30)
        cursor.execute(query, (hoje.strftime('%Y-%m-%d'), hoje.strftime('%Y-%m-%d'), proximidade_validade.strftime('%Y-%m-%d')))
        produtos_validade = cursor.fetchall()

        alertas = []
        for produto in produtos_validade:
            alertas.append({
                'nome': produto['nome'],
                'estoque': produto['estoqueAtual'],
                'validade': produto['dataValidade']
            })

        query_ruptura = '''
            SELECT p.nome, p.estoqueAtual, SUM(vp.quantidadeProduto) AS vendas_mes
            FROM produto p
            JOIN VendaProduto vp ON vp.produtoId = p.id
            JOIN Venda v ON vp.vendaId = v.id
            WHERE v.dataVenda BETWEEN ? AND ?
            GROUP BY p.id
            HAVING vendas_mes > p.estoqueAtual * 0.8
        '''
        ultimo_mes = hoje - timedelta(days=30)
        cursor.execute(query_ruptura, (ultimo_mes.strftime('%Y-%m-%d'), hoje.strftime('%Y-%m-%d')))
        produtos_ruptura = cursor.fetchall()

        for produto in produtos_ruptura:
            alertas.append({
                'nome': produto['nome'],
                'estoque': produto['estoqueAtual'],
                'vendas_mes': produto['vendas_mes']
            })

        conn.close()

        if alertas:
            enviar_email_alertas(alertas)
        
        return jsonify({'mensagem': 'Alertas de validade e ruptura enviados com sucesso!'}), 200
    except Exception as e:
        logging.error(f"Erro: {e}")
        return jsonify({'erro': str(e)}), 500

def enviar_email_alertas(alertas):
    try:
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        smtp_user = "kaytohf@gmail.com"
        smtp_password = "suum ezaa woxe mama"

        destinatario = "kaytohf@gmail.com"
        assunto = "Alertas de Validade e Estoque"
        
        mensagem = MIMEMultipart()
        mensagem['From'] = smtp_user
        mensagem['To'] = destinatario
        mensagem['Subject'] = assunto

        corpo_email = "<h2>Produtos em alerta de validade:</h2>"
        hoje = datetime.now().date()

        for alerta in alertas:
            validade_raw = alerta['validade']  # Captura o valor bruto da validade
            
            # Verifica se validade_raw é um inteiro (timestamp)
            if isinstance(validade_raw, int):
                validade = datetime.fromtimestamp(validade_raw / 1000)  # Converte de ms para datetime
            else:
                try:
                    validade = datetime.strptime(validade_raw, '%Y-%m-%d')  # Se for uma string
                except ValueError as e:
                    logging.error(f"Formato de validade inválido: {validade_raw}. Erro: {e}")
                    continue  # Pula se o formato for inválido

            if validade.date() < hoje:
                cor = "red"
            elif (validade.date() - hoje).days <= 7:
                cor = "orange"
            else:
                cor = "black"

            validade_str = validade.strftime('%d/%m/%Y')
            corpo_email += f"""
                <p style="color:{cor};">
                    <strong>Produto:</strong> {alerta['nome']}<br>
                    <strong>Estoque:</strong> {alerta['estoque']}<br>
                    <strong>Validade:</strong> {validade_str}<br>
                </p>
            """

        mensagem.attach(MIMEText(corpo_email, 'html'))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, destinatario, mensagem.as_string())
        
        logging.info("Email enviado com sucesso!")
    except smtplib.SMTPAuthenticationError:
        logging.error("Erro de autenticação ao tentar enviar o e-mail. Verifique suas credenciais.")
    except smtplib.SMTPException as e:
        logging.error(f"Erro ao enviar e-mail: {e}")
    except Exception as e:
        logging.error(f"Erro inesperado ao enviar e-mail: {e}")


@app.route('/api/consultar-produtos', methods=['GET'])
def consultar_produtos():
    try:
        nome_produto = request.args.get('nome')
        
        conn = connection_database()
        cursor = conn.cursor()

        # Consulta produtos pelo nome (se fornecido) ou retorna todos os produtos
        if nome_produto:
            cursor.execute('SELECT * FROM produto WHERE nome LIKE ?', ('%' + nome_produto + '%',))
        else:
            cursor.execute('SELECT * FROM produto')
        
        produtos = cursor.fetchall()
        conn.close()

        lista_produtos = [
            {
                'nome': produto['nome'],
                'preco': produto['preco'],
                'estoqueAtual': produto['estoqueAtual'],
                'dataValidade': datetime.fromtimestamp(int(produto['dataValidade']) / 1000).strftime('%d/%m/%Y'),
                'dataCadastro': datetime.fromtimestamp(int(produto['dataCadastro']) / 1000).strftime('%d/%m/%Y')
            }
            for produto in produtos
        ]

        return jsonify(lista_produtos), 200
    except Exception as e:
        print(f"Erro na rota /api/consultar-produtos: {e}")
        return jsonify({'erro': str(e)}), 500
@app.route('/api/desperdicio-produtos', methods=['GET'])
def desperdicio_produtos():
    try:
        conn = connection_database()
        cursor = conn.cursor()
        
        # Consulta para obter todos os produtos com estoque atual maior que 0
        query = '''
            SELECT nome, estoqueAtual AS desperdicio_total, dataValidade
            FROM produto
            WHERE estoqueAtual > 0
        '''
        cursor.execute(query)
        produtos = cursor.fetchall()
        conn.close()

        # Data atual para comparação
        data_atual = datetime.now().date()
        
        resultado = []
        for produto in produtos:
            # Verifica o tipo de dataValidade e faz a conversão apropriada
            data_validade_raw = produto['dataValidade']
            
            # Converte a dataValidade de timestamp para datetime.date
            if isinstance(data_validade_raw, str):
                # Tenta converter a string para datetime
                try:
                    data_validade = datetime.strptime(data_validade_raw, '%Y-%m-%d %H:%M:%S').date()
                except ValueError:
                    data_validade = datetime.strptime(data_validade_raw, '%Y-%m-%d').date()
            elif isinstance(data_validade_raw, (int, float)):
                # Trata como timestamp e converte para datetime
                data_validade = datetime.fromtimestamp(data_validade_raw / 1000).date()  # Divisão por 1000 para converter de ms para s
            else:
                # Se o formato não for reconhecido, pula este item
                continue

            # Verifica se a data de validade é anterior à data atual
            if data_validade < data_atual:
                resultado.append({
                    'nome': produto['nome'],
                    'desperdicio_total': produto['desperdicio_total'],
                    'data_validade': data_validade.strftime('%d/%m/%Y')  # Formato legível da data
                })

        return jsonify(resultado), 200
    except Exception as e:
        print(f"Erro na rota /api/desperdicio-produtos: {e}")
        return jsonify({'erro': str(e)}), 500
def iniciar_alertas_automaticamente():
    def agendar_alertas():
        while True:
            with app.app_context():  # Configura o contexto da aplicação para esta execução
                try:
                    logging.info("Executando alertas de validade e ruptura de estoque...")
                    alertas_validade_estoque()  # Apenas uma chamada
                    logging.info("Alerta enviado com sucesso!")
                except Exception as e:
                    logging.error(f"Erro ao enviar alertas de estoque: {e}")
            time.sleep(86400)  # Intervalo de 24 horas

    # Inicia a thread para execução dos alertas de estoque
    thread_alertas = threading.Thread(target=agendar_alertas)
    thread_alertas.daemon = True
    thread_alertas.start()


if __name__ == '__main__':
    iniciar_alertas_automaticamente()
    app.run(debug=True, port=8080)
