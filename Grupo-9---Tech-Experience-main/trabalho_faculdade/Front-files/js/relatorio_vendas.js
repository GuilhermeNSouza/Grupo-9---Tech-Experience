// Quando o botão "Gerar Relatório" é clicado, chama a função gerarRelatorio()
document.getElementById('Gerar_relatorio').addEventListener('click', gerarRelatorio);

async function gerarRelatorio() {
    const dataInicio = document.getElementById('data_comeco').value;
    const dataFim = document.getElementById('fim_data').value;

    if (!dataInicio || !dataFim) {
        alert('Por favor, selecione ambas as datas.');
        return;
    }

    const apiUrl = `http://127.0.0.1:8080/api/vendas?data_inicio=${dataInicio}&data_fim=${dataFim}`;

    try {
        const response = await fetch(apiUrl);
        const data = await response.json();

        if (!response.ok) {
            alert(`Erro: ${data.erro}`);
            return;
        }

        const tbody = document.getElementById('relatorio-corpo');
        tbody.innerHTML = '';

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

function filtrarTabela(tabelaId, valorFiltro) {
    const tabela = document.getElementById(tabelaId);
    const linhas = Array.from(tabela.getElementsByTagName("tr"));

    linhas.forEach(linha => {
        const nomeProduto = linha.cells[0].textContent.toLowerCase(); // O nome do produto está na primeira coluna
        if (nomeProduto.includes(valorFiltro.toLowerCase())) {
            linha.style.display = ""; // Mostra a linha se corresponder ao filtro
        } else {
            linha.style.display = "none"; // Oculta a linha se não corresponder
        }
    });
}

// Variáveis para alternar a ordem das colunas de "Total Valor" e "Quantidade Vendida"
let ordemCrescenteValor = true; 
let ordemCrescenteQuantidade = true; 

function ordenarPorTotalValor() {
    const tabela = document.getElementById("relatorio-corpo");
    const linhas = Array.from(tabela.getElementsByTagName("tr"));

    // Ordena as linhas da tabela pela coluna "Total Valor"
    linhas.sort((a, b) => {
        const valorA = parseFloat(a.cells[3].textContent.replace('R$', '').replace(',', ''));
        const valorB = parseFloat(b.cells[3].textContent.replace('R$', '').replace(',', ''));
        return ordemCrescenteValor ? valorA - valorB : valorB - valorA;
    });

    // Reinsere as linhas na tabela em ordem
    tabela.innerHTML = '';
    linhas.forEach(linha => tabela.appendChild(linha));

    // Alterna a ordem para a próxima vez que a função for chamada
    ordemCrescenteValor = !ordemCrescenteValor;
    document.getElementById('ordenar-valor').textContent = ordemCrescenteValor ? "⬆" : "⬇";
}

function ordenarPorQuantidadeVendida() {
    const tabela = document.getElementById("relatorio-corpo");
    const linhas = Array.from(tabela.getElementsByTagName("tr"));

    // Ordena as linhas da tabela pela coluna "Quantidade Vendida"
    linhas.sort((a, b) => {
        const quantidadeA = parseInt(a.cells[2].textContent);
        const quantidadeB = parseInt(b.cells[2].textContent);
        return ordemCrescenteQuantidade ? quantidadeA - quantidadeB : quantidadeB - quantidadeA;
    });

    // Reinsere as linhas na tabela em ordem
    tabela.innerHTML = '';
    linhas.forEach(linha => tabela.appendChild(linha));

    // Alterna a ordem para a próxima vez que a função for chamada
    ordemCrescenteQuantidade = !ordemCrescenteQuantidade;
    document.getElementById('ordenar-quantidade').textContent = ordemCrescenteQuantidade ? "⬆" : "⬇";
}

function filtrarTabela(tabelaId, valorFiltro) {
    const tabela = document.getElementById(tabelaId);
    const linhas = Array.from(tabela.getElementsByTagName("tr"));

    // Remove as linhas que não correspondem ao filtro
    linhas.forEach(linha => {
        const nomeProduto = linha.cells[0].textContent.toLowerCase(); // O nome do produto está na primeira coluna
        if (nomeProduto.includes(valorFiltro.toLowerCase())) {
            linha.style.display = ""; // Mostra a linha se corresponder ao filtro
        } else {
            linha.style.display = "none"; // Oculta a linha se não corresponder
        }
    });
}
