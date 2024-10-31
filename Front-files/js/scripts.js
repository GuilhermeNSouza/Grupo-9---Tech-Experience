document.addEventListener("DOMContentLoaded", () => {
    // Seleciona as seções
    const relatorioVendas = document.getElementById('relatorio-vendas');
    const alertaValidade = document.getElementById('alerta-validade');
    const previsaoDemanda = document.getElementById('previsao-demanda');

    // Seleciona os itens do menu
    const menuRelatorio = document.querySelector('a[href="#relatorio-vendas"]');
    const menuAlerta = document.querySelector('a[href="#alerta-validade"]');
    const menuPrevisao = document.querySelector('a[href="#previsao-demanda"]');

    // Verifique se todos os elementos foram encontrados antes de continuar
    if (!relatorioVendas || !alertaValidade || !previsaoDemanda || !graficoPrincipal || 
        !menuRelatorio || !menuAlerta || !menuPrevisao || !menuPrincipal) {
        console.error("Um ou mais elementos não foram encontrados no DOM.");
        return;
    }

    // Função para mostrar a seção e ocultar as outras
    function mostrarSecao(secao) {
        // Oculta todas as seções primeiro
        relatorioVendas.style.display = 'none';
        alertaValidade.style.display = 'none';
        previsaoDemanda.style.display = 'none';
        graficoPrincipal.style.display = 'none';

        // Exibe a seção selecionada
        secao.style.display = 'block';
    }

    // Exibe o gráfico de alertas na tela inicial

    menuRelatorio.addEventListener('click', (e) => {
        e.preventDefault();
        mostrarSecao(relatorioVendas);
    });

    menuAlerta.addEventListener('click', (e) => {
        e.preventDefault();
        mostrarSecao(alertaValidade);
    });

    menuPrevisao.addEventListener('click', (e) => {
        e.preventDefault();
        mostrarSecao(previsaoDemanda);
    });

    // Event listener para retornar ao gráfico principal
});
