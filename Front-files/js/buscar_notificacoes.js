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

        // Armazena notificações para pesquisa
        produtos.forEach(produto => {
            const dataValidade = new Date(Number(produto.validade));
            const diasRestantes = Math.ceil((dataValidade - hoje) / (1000 * 60 * 60 * 24));

            const notificacao = document.createElement('div');
            notificacao.className = 'notificacao';

            if (diasRestantes <= 7) {
                notificacao.classList.add('alerta-validade');
            }

            const dataValidadeFormatada = dataValidade.toLocaleDateString('pt-BR');

            notificacao.innerHTML = `
                <h3>${produto.nome}</h3>
                <p>Quantidade em estoque: ${produto.quantidade}</p>
                <p>Data de validade: ${dataValidadeFormatada} (${diasRestantes} dias restantes)</p>
            `;
            listaNotificacoes.appendChild(notificacao);
        });
    } catch (error) {
        console.error('Erro ao buscar notificações de validade:', error);
    }
}

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

document.addEventListener('DOMContentLoaded', buscarNotificacoes);
