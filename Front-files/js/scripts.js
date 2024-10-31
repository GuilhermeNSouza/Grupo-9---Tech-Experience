document.addEventListener('DOMContentLoaded', function () {
    const sections = ['dashboard-container', 'relatorio-vendas', 'alerta-validade', 'previsao-demanda'];
    const sidebarLinks = document.querySelectorAll('.sidebar-menu a');

    // Função para mostrar a seção correta
    function mostrarSecao(secaoId) {
        sections.forEach(id => {
            const section = document.getElementById(id);
            section.style.display = (id === secaoId) ? 'block' : 'none';
        });
    }

    // Event listener para os links da sidebar
    sidebarLinks.forEach(link => {
        link.addEventListener('click', function (event) {
            event.preventDefault(); // Previne a navegação padrão do link
            const secaoId = this.getAttribute('data-section');
            mostrarSecao(secaoId);
        });
    });

});
// Função para filtrar as tabelas de cada seção
function filtrarTabela(tabelaId, filtro) {
    const tabela = document.getElementById(tabelaId);
    const linhas = tabela.getElementsByTagName('tr');
    const filtroMinusculo = filtro.toLowerCase();

    // Itera pelas linhas da tabela e exibe apenas as que correspondem ao filtro
    for (let i = 0; i < linhas.length; i++) {
        const colunaProduto = linhas[i].getElementsByTagName('td')[0];
        if (colunaProduto) {
            const textoProduto = colunaProduto.textContent || colunaProduto.innerText;
            linhas[i].style.display = textoProduto.toLowerCase().includes(filtroMinusculo) ? '' : 'none';
        }
    }
}
