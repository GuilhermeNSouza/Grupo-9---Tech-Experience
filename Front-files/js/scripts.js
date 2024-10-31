function mostrarSecao(secaoId) {
    const secoes = ['dashboard-container', 'relatorio-vendas', 'alerta-validade', 'previsao-demanda'];

    // Itera sobre todas as seções e exibe a seção correspondente
    secoes.forEach(id => {
        const secao = document.getElementById(id);
        if (secao) {
            secao.style.display = (id === secaoId) ? 'block' : 'none';
        }
    });

    // Se estiver na aba de notificações, buscar as notificações
    if (secaoId === 'notificacoes-validade') {
        buscarNotificacoes();
    }
}
