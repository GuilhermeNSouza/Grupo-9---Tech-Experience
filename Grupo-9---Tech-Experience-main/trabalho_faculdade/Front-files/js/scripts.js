document.addEventListener('DOMContentLoaded', function () {
    const sections = ['dashboard-container', 'relatorio-vendas', 'alerta-validade', 'previsao-demanda', 'controle-estoque','sugestao-reposicao','sugestao-descontos','container','promocao'];
    const sidebarLinks = document.querySelectorAll('.sidebar-menu a');

    // Função para mostrar a seção correta
    function mostrarSecao(secaoId) {
        sections.forEach(id => {
            const section = document.getElementById(id);
            if (section) {
                section.style.display = (id === secaoId) ? 'block' : 'none';
            }
        });

        // Carrega dados específicos quando necessário
        if (secaoId === 'alerta-validade') {
            buscarNotificacoes(); // Função para buscar notificações de validade
        } else if (secaoId === 'previsao-demanda') {
        } else if (secaoId === 'controle-estoque') {
            carregarControleEstoque(); // Função para carregar dados de controle de estoque
        }
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