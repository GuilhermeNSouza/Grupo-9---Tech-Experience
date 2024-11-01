async function atualizarInfoCards() {
    try {
        const responseVendas = await fetch('http://127.0.0.1:8080/api/vendas?data_inicio=2024-01-01&data_fim=2024-12-31');
        const vendas = await responseVendas.json();

        const produtoMaisVendido = vendas.reduce((max, produto) => produto.quantidade_vendida > max.quantidade_vendida ? produto : max, vendas[0]);
        document.getElementById('produto-mais-vendido').textContent = `${produtoMaisVendido.nome_produto} (${produtoMaisVendido.quantidade_vendida} unidades)`;

        const lucroTotal = vendas.reduce((total, produto) => total + produto.total_vendas, 0);
        document.getElementById('lucro-total').textContent = `R$ ${lucroTotal.toLocaleString('pt-BR')}`;

        const responseNotificacoes = await fetch('http://127.0.0.1:8080/api/notificacoes-validade');
        const notificacoes = await responseNotificacoes.json();
        const produtosVencidos = notificacoes.filter(produto => new Date(Number(produto.validade)) < new Date()).length;
        const alertasValidade = notificacoes.filter(produto => {
            const diasRestantes = (new Date(Number(produto.validade)) - new Date()) / (1000 * 60 * 60 * 24);
            return diasRestantes > 0 && diasRestantes <= 10;
        }).length;

        document.getElementById('produtos-vencidos').textContent = produtosVencidos;
        document.getElementById('alertas-validade').textContent = alertasValidade;
    } catch (error) {
        console.error('Erro ao atualizar os cards de informações:', error);
    }
}
// Função para gerar o gráfico de lucro e o ranking de previsão
async function gerarGraficoEListaPrevisao() {
    try {
        // Obter dados reais de vendas
        const responseVendas = await fetch('http://127.0.0.1:8080/api/vendas?data_inicio=2024-01-01&data_fim=2024-12-31');
        const vendas = await responseVendas.json();

        // Selecionar os 10 produtos com maior lucro
        const topProdutosLucro = vendas
            .sort((a, b) => b.total_vendas - a.total_vendas)
            .slice(0, 10); 

        const labelsLucro = topProdutosLucro.map(produto => produto.nome_produto);
        const dataLucro = topProdutosLucro.map(produto => produto.total_vendas);

        const colorsPastel = [
            '#A3C4BC', '#E3D5CA', '#C3B299', '#D1B1C8', '#92A8D1', 
            '#F7CAC9', '#B5EAD7', '#FFDAC1', '#FF9AA2', '#C7CEEA'
        ];

        // Gráfico de Lucro com valores exibidos dentro do círculo
        const ctxLucro = document.getElementById('graficoLucro').getContext('2d');
        new Chart(ctxLucro, {
            type: 'doughnut',
            data: {
                labels: labelsLucro,
                datasets: [{
                    data: dataLucro,
                    backgroundColor: colorsPastel,
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    datalabels: {
                        color: '#333',
                        font: {
                            weight: 'bold'
                        },
                        formatter: (value, ctx) => {
                            let label = ctx.chart.data.labels[ctx.dataIndex];
                            return `${label}\nR$ ${value.toLocaleString('pt-BR')}`;
                        },
                        anchor: 'center',
                        align: 'center',
                        clamp: true
                    }
                },
                cutout: '70%', // Aumenta o espaço central
            },
            plugins: [ChartDataLabels]
        });

    } catch (error) {
        console.error("Erro ao gerar gráfico de lucro e ranking de previsão:", error);
    }
}

// Carrega as informações e o gráfico ao carregar a página
document.addEventListener('DOMContentLoaded', () => {
    atualizarInfoCards();
    gerarGraficoEListaPrevisao();
});

// Função para buscar notificações de validade
async function buscarNotificacoes() {
    try {
        const response = await fetch('http://127.0.0.1:8080/api/notificacoes-validade');
        const produtos = await response.json();

        const listaNotificacoes = document.getElementById('lista-notificacoes');
        listaNotificacoes.innerHTML = '';  // Limpa notificações anteriores

        if (produtos.length === 0) {
            listaNotificacoes.innerHTML = '<p>Não há produtos registrados.</p>';
            return;
        }

        const hoje = new Date();

        // Armazena notificações para pesquisa e exibe alertas para produtos perto de vencer e já vencidos
        produtos.forEach(produto => {
            const dataValidade = new Date(Number(produto.validade));
            const diasRestantes = Math.ceil((dataValidade - hoje) / (1000 * 60 * 60 * 24));

            const notificacao = document.createElement('div');
            notificacao.className = 'notificacao';

            if (diasRestantes < 0) { // Produto já vencido
                notificacao.classList.add('alerta-vencido');
                notificacao.innerHTML = `
                    <h3>${produto.nome}</h3>
                    <p>Quantidade em estoque: ${produto.quantidade}</p>
                    <p style="color: red;"><strong>Produto Vencido!</strong> Venceu em: ${dataValidade.toLocaleDateString('pt-BR')}</p>
                `;
            } else if (diasRestantes <= 10) { // Produto com menos de 10 dias para vencer
                notificacao.classList.add('alerta-validade');
                notificacao.innerHTML = `
                    <h3>${produto.nome}</h3>
                    <p>Quantidade em estoque: ${produto.quantidade}</p>
                    <p>Data de validade: ${dataValidade.toLocaleDateString('pt-BR')} (<span style="color: orange;">${diasRestantes} dias restantes</span>)</p>
                `;
            } else {
                notificacao.innerHTML = `
                    <h3>${produto.nome}</h3>
                    <p>Quantidade em estoque: ${produto.quantidade}</p>
                    <p>Data de validade: ${dataValidade.toLocaleDateString('pt-BR')} (${diasRestantes} dias restantes)</p>
                `;
            }

            listaNotificacoes.appendChild(notificacao);
        });
    } catch (error) {
        console.error('Erro ao buscar notificações de validade:', error);
    }
}

document.addEventListener('DOMContentLoaded', buscarNotificacoes);


// Função para gerar a previsão mensal ajustada para o mês passado
async function gerarPrevisaoMensalMesPassado() {
    try {
        // po esses parametros aqui e foda eu ia colocar date time mas a bosta do banco de dados nao tem os valores, pelo amor de deus ue banco de dados RUIM CARA ERA PARA ESTAR FUNCIONANDO O CADASTRAR PRODUTOS SE NAO FOSSE TAO RUIM 
        const dataInicio = '2024-09-01';
        const dataFim = '2024-10-30';
        
        // Faz a requisição para a API com os parâmetros de data
        const response = await fetch(`http://127.0.0.1:8080/api/previsao_demanda_mensal?data_inicio=${dataInicio}&data_fim=${dataFim}`);
        
        // Verifica se a resposta da API está OK
        if (!response.ok) {
            throw new Error(`Erro na API: ${response.statusText}`);
        }
        
        const previsoes = await response.json();
        
        // Seleciona o elemento da tabela e limpa o conteúdo
        const corpoRanking = document.getElementById('corpo-ranking-previsao');
        corpoRanking.innerHTML = ''; // Limpa a tabela antes de adicionar novos dados

        // Adiciona os 10 produtos com maior previsão à tabela
        previsoes.slice(0, 10).forEach(produto => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${produto.produto}</td>
                <td>${produto.total_previsto_proximo_mes} unidades</td>
            `;
            corpoRanking.appendChild(row);
        });

    } catch (error) {
        console.error("Erro ao gerar previsão mensal para o mês passado:", error);
    }
}

// Função para carregar as informações e o gráfico ao carregar a página
document.addEventListener('DOMContentLoaded', () => {
    atualizarInfoCards(); // Carrega os cartões de informações
    gerarPrevisaoMensalMesPassado(); // Gera a previsão mensal para o mês passado
});



async function obterDadosDesperdicio() {
    try {
        const resposta = await fetch('http://127.0.0.1:8080/api/desperdicio-produtos');
        const dados = await resposta.json();

        if (!Array.isArray(dados) || dados.length === 0) {
            console.error("Nenhum dado de desperdício encontrado.");
            return;
        }

        // Ordena os produtos pelo desperdício total em ordem decrescente e pega os 15 maiores
        const dadosFiltrados = dados.sort((a, b) => b.desperdicio_total - a.desperdicio_total).slice(0, 15);

        const nomesProdutos = dadosFiltrados.map(item => item.nome);
        const desperdicioTotal = dadosFiltrados.map(item => item.desperdicio_total);

        // Cria o gráfico de desperdício com os dados filtrados
        criarGraficoDesperdicio(nomesProdutos, desperdicioTotal);

        // Exibe os dados no console para depuração (opcional)
        console.log("Produtos com desperdício:", dadosFiltrados);
    } catch (error) {
        console.error("Erro ao buscar dados de desperdício:", error);
    }
}

// Chama a função ao carregar a página ou em um evento específico
document.addEventListener('DOMContentLoaded', obterDadosDesperdicio);


function criarGraficoDesperdicio(nomes, desperdicios) {
    const ctx = document.getElementById('graficoDesperdicio').getContext('2d');

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: nomes,
            datasets: [{
                label: 'Desperdício Total (unidades)',
                data: desperdicios,
                backgroundColor: 'rgba(255, 99, 132, 0.5)',
                borderColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            indexAxis: 'y',  // Configura o gráfico para exibir barras horizontais
            scales: {
                x: {
                    beginAtZero: true
                },
                y: {
                    beginAtZero: true
                }
            },
            plugins: {
                legend: {
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.raw} unidades`;
                        }
                    }
                }
            }
        }
    });
}

// Chama a função para obter os dados e criar o gráfico
obterDadosDesperdicio();
