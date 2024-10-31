// Função para buscar notificações de validade
async function buscarNotificacoes() {
    try {
        // Faz a requisição para a API de notificações de validade
        const response = await fetch('http://127.0.0.1:8080/api/notificacoes-validade');
        const produtos = await response.json();

        // Elemento onde as notificações serão exibidas
        const listaNotificacoes = document.getElementById('lista-notificacoes');
        listaNotificacoes.innerHTML = '';  // Limpa notificações anteriores

        // Verifica se há produtos
        if (produtos.length === 0) {
            listaNotificacoes.innerHTML = '<p>Não há produtos registrados.</p>';
            return;
        }

        const hoje = new Date();

        // Armazena notificações para pesquisa e exibe alertas especiais para produtos perto de vencer e já vencidos
        produtos.forEach(produto => {
            const dataValidade = new Date(Number(produto.validade)); // Converte o timestamp para uma data
            const diasRestantes = Math.ceil((dataValidade - hoje) / (1000 * 60 * 60 * 24)); // Calcula os dias restantes

            const notificacao = document.createElement('div');
            notificacao.className = 'notificacao';

            // Define a cor do alerta dependendo dos dias restantes
            if (diasRestantes < 0) { // Produto já vencido
                notificacao.classList.add('alerta-vencido');
                notificacao.innerHTML = `
                    <h3>${produto.nome}</h3>
                    <p>Quantidade em estoque: ${produto.quantidade}</p>
                    <p style="color: red;"><strong>Produto Vencido!</strong>  Venceu em: ${dataValidade.toLocaleDateString('pt-BR')}</p>
                `;
            } else if (diasRestantes <= 10) { // Produto com menos de 10 dias para vencer
                notificacao.classList.add('alerta-validade');
                notificacao.innerHTML = `
                    <h3>${produto.nome}</h3>
                    <p>Quantidade em estoque: ${produto.quantidade}</p>
                    <p>Data de validade: ${dataValidade.toLocaleDateString('pt-BR')} (<span style="color: orange;">${diasRestantes} dias restantes</span>)</p>
                `;
            } else {
                // Exibe normalmente produtos com validade acima de 10 dias
                notificacao.innerHTML = `
                    <h3>${produto.nome}</h3>
                    <p>Quantidade em estoque: ${produto.quantidade}</p>
                    <p>Data de validade: ${dataValidade.toLocaleDateString('pt-BR')} (${diasRestantes} dias restantes)</p>
                `;
            }

            listaNotificacoes.appendChild(notificacao); // Adiciona a notificação na lista
        });
    } catch (error) {
        console.error('Erro ao buscar notificações de validade:', error);
    }
}

// Função para filtrar notificações com base no nome do produto
function filtrarNotificacoes() {
    const input = document.getElementById('filtro-notificacoes').value.toLowerCase();
    const notificacoes = document.querySelectorAll('#lista-notificacoes .notificacao');
    
    notificacoes.forEach(notificacao => {
        const nomeProduto = notificacao.querySelector('h3').innerText.toLowerCase();
        if (nomeProduto.includes(input)) {
            notificacao.style.display = 'block';
        } else {
            notificacao.style.display = 'none';
        }
    });
}

// Chama a função de busca de notificações ao carregar a página
document.addEventListener('DOMContentLoaded', buscarNotificacoes);
