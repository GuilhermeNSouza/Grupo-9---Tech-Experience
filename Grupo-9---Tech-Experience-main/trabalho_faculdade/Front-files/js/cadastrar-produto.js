

// ESSA MERDA AQUI SO FUNCIONA O CONSULTAR PRODUTOS NAO TENTE CADASTRAR POIS O BANCO DE DADOS DA UM ERRO DE LOCKED TENTEI DE TUDO MAS NAO DA ENTAO DESISTA
document.getElementById('formCadastro').addEventListener('submit', async function (e) {
    e.preventDefault();
    
    const produto = {
        nome: document.getElementById('nome').value,
        preco: parseFloat(document.getElementById('preco').value),
        estoqueAtual: parseInt(document.getElementById('estoqueAtual').value),
        dataValidade: new Date(document.getElementById('dataValidade').value).getTime()
    };

    try {
        const response = await fetch('http://127.0.0.1:8080/api/cadastrar-produto', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(produto)
        });
        
        const resultado = await response.json();
        alert(resultado.mensagem || resultado.erro);
        document.getElementById('formCadastro').reset();
    } catch (error) {
        console.error('Erro ao cadastrar produto:', error);
    }
});

// Função para consultar produtos
async function consultarProdutos() {
    const nomeProduto = document.getElementById('buscaNome').value;
    const url = nomeProduto 
        ? `http://127.0.0.1:8080/api/consultar-produtos?nome=${nomeProduto}`
        : 'http://127.0.0.1:8080/api/consultar-produtos';

    try {
        const response = await fetch(url);
        const produtos = await response.json();

        const listaProdutos = document.getElementById('listaProdutos');
        listaProdutos.innerHTML = '';

        produtos.forEach(produto => {
            const item = document.createElement('li');
            item.innerHTML = `
                <strong>Nome:</strong> ${produto.nome}<br>
                <strong>Preço:</strong> R$ ${produto.preco.toFixed(2)}<br>
                <strong>Estoque Atual:</strong> ${produto.estoqueAtual}<br>
                <strong>Data de Validade:</strong> ${produto.dataValidade}<br>
                <strong>Data de Cadastro:</strong> ${produto.dataCadastro}<br><br>
            `;
            listaProdutos.appendChild(item);
        });
    } catch (error) {
        console.error('Erro ao consultar produtos:', error);
    }
}
