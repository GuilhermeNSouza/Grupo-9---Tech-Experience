async function gerarPrevisaoMensal() {
    try {
        const response = await fetch(`http://127.0.0.1:8080/api/previsao_demanda_mensal`);
        const previsoes = await response.json();

        const corpoPrevisao = document.getElementById('corpo-previsao-todos');
        corpoPrevisao.innerHTML = ''; // Limpa a tabela anterior

        // Adiciona cada previsão de produto na tabela
        previsoes.forEach(produto => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${produto.produto}</td>
                <td>${produto.total_previsto_proximo_mes}</td>
            `;
            corpoPrevisao.appendChild(row);
        });
    } catch (error) {
        console.error("Erro ao buscar previsão de demanda mensal:", error);
    }
}

// Botão para carregar as previsões mensais
document.getElementById('botao-previsao').addEventListener('click', gerarPrevisaoMensal);
