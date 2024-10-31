function mostrarSecao(secaoId) {
    const secoes = ['relatorio-vendas', 'alerta-validade', 'previsao-demanda', 'notificacoes-validade'];
    
    // Itera sobre todas as seções
    secoes.forEach(id => {
        const secao = document.getElementById(id);
        if (secao) {
            // Mostra a seção correspondente ao id selecionado e oculta as outras
            secao.style.display = (id === secaoId) ? 'block' : 'none';
        }
    });

    // Se estiver na aba de notificações, buscar as notificações
    if (secaoId === 'notificacoes-validade') {
        buscarNotificacoes();
    }
}
