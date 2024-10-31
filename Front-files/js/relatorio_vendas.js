document.getElementById('Gerar_relatorio').addEventListener('click', gerarRelatorio);

async function gerarRelatorio() {
    // Obtenha as datas do formulário
    const dataInicio = document.getElementById('data_comeco').value;
    const dataFim = document.getElementById('fim_data').value;

    if (!dataInicio || !dataFim) {
        alert('Por favor, selecione ambas as datas.');
        return;
    }

    // Construir a URL da API com os parâmetros de data
    const apiUrl = `http://127.0.0.1:8080/api/vendas?data_inicio=${dataInicio}&data_fim=${dataFim}`;

    try {
        // Fazer requisição para a API
        const response = await fetch(apiUrl);
        const data = await response.json();

        if (!response.ok) {
            alert(`Erro: ${data.erro}`);
            return;
        }

        // Limpar a tabela de relatórios
        const tbody = document.getElementById('relatorio-corpo');
        tbody.innerHTML = '';

        // Exibir os dados na tabela
        data.forEach((item) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${item.nome_produto}</td>
                <td>${item.quantidade_estoque}</td>
                <td>${item.quantidade_vendida}</td>
                <td>R$ ${item.total_vendas.toFixed(2)}</td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Erro ao obter o relatório de vendas:', error);
    }
}
