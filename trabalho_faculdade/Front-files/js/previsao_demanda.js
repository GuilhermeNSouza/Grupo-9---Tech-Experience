async function gerarPrevisaoDemanda() {
    try {
        const dataInicio = document.getElementById('data_inicio_previsao').value;
        const dataFim = document.getElementById('data_fim_previsao').value;

        if (!dataInicio || !dataFim) {
            alert("Por favor, selecione as datas de início e fim para gerar a previsão.");
            return;
        }

        // Envia as datas no formato YYYY-MM-DD diretamente para a API
        const response = await fetch(`http://127.0.0.1:8080/api/previsao_demanda_sazonal?data_inicio=${dataInicio}&data_fim=${dataFim}`);
        
        if (!response.ok) {
            throw new Error("Erro ao buscar dados de previsão de demanda: " + response.statusText);
        }

        const previsoes = await response.json();

        // Ordena as previsões do maior para o menor com base na média mensal prevista
        previsoes.sort((a, b) => b.media_mensal_prevista - a.media_mensal_prevista);

        const corpoPrevisao = document.getElementById('corpo-previsao-todos');
        corpoPrevisao.innerHTML = ''; // Limpa a tabela anterior

        // Adiciona as previsões à tabela com valores arredondados
        previsoes.forEach(({ produto, media_mensal_prevista }) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${produto}</td>
                <td>${Math.round(media_mensal_prevista)} unidades</td>
            `;
            corpoPrevisao.appendChild(row);
        });

    } catch (error) {
        console.error("Erro ao buscar dados de previsão de demanda:", error);
    }
}

document.getElementById('botao-previsao').addEventListener('click', gerarPrevisaoDemanda);


// Função para filtrar a tabela de previsões sazonais
function filtrarTabelaPrevisao() {
    const input = document.getElementById('pesquisar-previsao-todos').value.toLowerCase();
    const tabela = document.getElementById('tabela-previsao-todos');
    const linhas = tabela.getElementsByTagName('tr');

    for (let i = 1; i < linhas.length; i++) { // Começa de 1 para ignorar o cabeçalho
        const linha = linhas[i];
        const colunaProduto = linha.getElementsByTagName('td')[0]; // A primeira coluna (Produto)

        if (colunaProduto) {
            const textoProduto = colunaProduto.textContent || colunaProduto.innerText;
            linha.style.display = textoProduto.toLowerCase().includes(input) ? '' : 'none';
        }
    }
}
