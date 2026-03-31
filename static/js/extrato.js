document.addEventListener('DOMContentLoaded', function() {
  // ======================== DOM Elements ========================
  const transacoesCards = document.querySelectorAll('.transacao-card');
  const dataInicio = document.getElementById('data-inicio');
  const dataFim = document.getElementById('data-fim');
  const tipoFiltro = document.getElementById('tipo-filtro');
  const limparBtn = document.getElementById('limpar-filtros');
  const totalSpan = document.getElementById('total-transacoes');
  const emptyState = document.querySelector('.empty-state');

  console.log('✅ DOM carregado. Cards encontrados:', transacoesCards.length);

  // ======================== Helper Functions ========================
  function atualizarContador(visiveis) {
    totalSpan.textContent = visiveis;
    if (transacoesCards.length === 0) {
      if (emptyState) emptyState.style.display = '';
      return;
    }
    if (visiveis === 0) {
      if (emptyState) emptyState.style.display = '';
    } else {
      if (emptyState) emptyState.style.display = 'none';
    }
  }

  function aplicarFiltros() {
    const inicio = dataInicio.value ? new Date(dataInicio.value) : null;
    const fim = dataFim.value ? new Date(dataFim.value) : null;
    const tipo = tipoFiltro.value;
    let visiveis = 0;

    transacoesCards.forEach(card => {
      const dataCardStr = card.getAttribute('data-data');
      const dataCard = new Date(dataCardStr);
      const tipoCard = card.getAttribute('data-tipo');
      let mostrar = true;

      if (inicio && dataCard < inicio) mostrar = false;
      if (fim && dataCard > fim) mostrar = false;
      if (tipo !== 'all' && tipoCard !== tipo) mostrar = false;

      if (mostrar) {
        card.style.display = '';
        visiveis++;
      } else {
        card.style.display = 'none';
      }
    });

    atualizarContador(visiveis);
  }

  function corrigirPixRecebido() {
    console.log('🔧 Iniciando correção...');
    let corrigidos = 0;

    transacoesCards.forEach(card => {
      const descricao = card.querySelector('.descricao')?.innerText || '';
      const tipoBadge = card.querySelector('.tipo-badge');
      const valorDiv = card.querySelector('.valor');
      const iconeDiv = card.querySelector('.card-icon i');

      const isPixRecebido = descricao.toLowerCase().includes('recebido via pix') || 
                            descricao.includes('PIX_RECEBIDO');

      if (isPixRecebido && tipoBadge?.classList.contains('debito')) {
        console.log('✅ Corrigindo:', descricao.substring(0, 50));

        tipoBadge.classList.remove('debito');
        tipoBadge.classList.add('deposito');
        tipoBadge.innerText = 'DEPÓSITO';

        valorDiv.classList.remove('negativo');
        valorDiv.classList.add('positivo');
        let valorTexto = valorDiv.innerText;
        if (valorTexto.startsWith('-')) {
          valorDiv.innerText = '+' + valorTexto.substring(1);
        }

        if (iconeDiv) {
          iconeDiv.classList.remove('fa-arrow-up');
          iconeDiv.classList.add('fa-arrow-down');
        }

        card.setAttribute('data-tipo', 'deposito');

        corrigidos++;
      }
    });

    console.log(`🏁 Correção finalizada. ${corrigidos} transações ajustadas.`);
  }

  function limparFiltros() {
    dataInicio.value = '';
    dataFim.value = '';
    tipoFiltro.value = 'all';
    aplicarFiltros();
  }

  // ======================== Inicialização ========================
  corrigirPixRecebido();
  aplicarFiltros();

  // ======================== Listeners ========================
  dataInicio.addEventListener('change', aplicarFiltros);
  dataFim.addEventListener('change', aplicarFiltros);
  tipoFiltro.addEventListener('change', aplicarFiltros);
  limparBtn.addEventListener('click', limparFiltros);

  // ======================== Toast Helper ========================
  function showToast(message, isError = false) {
    const toast = document.getElementById('toast');
    if (!toast) return;
    toast.textContent = message;
    toast.style.background = isError ? '#b91c1c' : '#10b981';
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3000);
  }
});