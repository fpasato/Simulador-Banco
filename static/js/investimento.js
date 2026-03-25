document.addEventListener('DOMContentLoaded', () => {

    let ultimoRecargaHistorico = null;

    // ========== Elementos DOM ==========
    const modal = document.getElementById('modal-overlay');
    const btnClose = document.querySelector('.close-modal');
    const modalTitulo = document.getElementById('modal-titulo');
    const modalRisco = document.getElementById('modal-risco');
    const modalInfo = document.getElementById('modal-info');
    const modalPrecoCota = document.getElementById('modal-preco');
    const modalValorCarteiraEl = document.getElementById('modal-valor-carteira');
    const modalSaldoContaEl = document.getElementById('modal-saldo-conta');
    const modalCarteiraExtra = document.getElementById('modal-carteira-extra');
    const modalQtdCarteiraEl = document.getElementById('modal-qtd-carteira');
    const modalLucroPrejuizoEl = document.getElementById('modal-lucro-prejuizo');
    const formComprar = document.getElementById('form-comprar');
    const inputInvestimentoIdComprar = document.getElementById('input-investimento-id');
    const inputQuantidadeComprar = document.getElementById('input-quantidade-compra');
    const modalTotalCompraEl = document.getElementById('modal-total-compra');
    const saldoAtualEl = document.getElementById('saldo-atual');
    const modalHistoricoCanvas = document.getElementById('modal-historico-chart');
    const timeoutsPreco = new Map();
    let modalPriceTimeout = null;
    const ultimosPrecos = new Map(); 
    // ========== Estado ==========
    let modalHistoricoChartInstance = null;
    let currentInvestimentoId = null;
    let currentPreco = 0;
    let currentQuantidadeCarteira = null; 
    let currentUniqueId = null;
    let ultimoServerTime = null;
    let ultimoLocalTime = null;

    // ========== Utilitários ==========
    const formatBRL = (value) => {
        const n = Number(value);
        if (!Number.isFinite(n)) return 'R$ 0,00';
        return `R$ ${n.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    };

    const formatarTempoRestante = (expiraTimestamp, agora) => {
        if (!expiraTimestamp) return '';
        const agoraTimestamp = agora !== undefined ? agora : ultimoServerTime;
        if (!agoraTimestamp) return '';
        let diff = expiraTimestamp - agoraTimestamp;
        if (diff <= 0) return 'expirado';
        const horas = Math.floor(diff / 3600);
        const minutos = Math.floor((diff % 3600) / 60);
        const segundos = diff % 60;
        if (horas > 0) {
            return `${horas.toString().padStart(2, '0')}:${minutos.toString().padStart(2, '0')}:${segundos.toString().padStart(2, '0')}`;
        } else {
            return `${minutos.toString().padStart(2, '0')}:${segundos.toString().padStart(2, '0')}`;
        }
    };

    const parsePositiveFloat = (value, fallback = 1) => {
        const n = parseFloat(value);
        return (!Number.isFinite(n) || n <= 0) ? fallback : n;
    };

    const parsePositiveInt = (value, fallback = 1) => {
    const n = parseInt(value);
    return (!Number.isFinite(n) || n <= 0) ? fallback : n;
};

    const formatarDataParaExibicao = (dataISO) => {
        try {
            const d = new Date(dataISO);
            return `${d.getDate().toString().padStart(2,'0')}/${(d.getMonth()+1).toString().padStart(2,'0')} ${d.getHours().toString().padStart(2,'0')}:${d.getMinutes().toString().padStart(2,'0')}`;
        } catch {
            return dataISO;
        }
    };

    const aplicarCoresRisco = (risco) => {
        const riscoLower = (risco || '').toLowerCase();
        const styles = {
            alto: { background: '#fee2e2', color: '#ef4444' },
            médio: { background: '#fef3c7', color: '#f59e0b' },
            medio: { background: '#fef3c7', color: '#f59e0b' },
            baixo: { background: '#dcfce7', color: '#22c55e' }
        };
        const style = styles[riscoLower] || { background: '#f1f5f9', color: '#64748b' };
        Object.assign(modalRisco.style, style);
    };

    // ========== LocalStorage ==========
    function salvarInvestimentosNoStorage(carteira) {
        const investimentosStorage = {};
        carteira.forEach(item => {
            if (item.temporario && item.tempo_restante > 0) {
                investimentosStorage[item.id] = {
                    id: item.id,
                    investimentoId: item.investimento_id,
                    nome: item.nome,
                    quantidade: item.quantidade,
                    saldo: item.saldo,
                    lucroPrejuizo: item.lucro_prejuizo,
                    tempo_restante: item.tempo_restante,
                    tempo_inicio: item.tempo_inicio,
                    duracao: item.duracao,
                    temporario: true
                };
            }
        });
        localStorage.setItem('investimentos_temporarios', JSON.stringify(investimentosStorage));
    }

    function carregarInvestimentosDoStorage() {
        const storage = localStorage.getItem('investimentos_temporarios');
        if (!storage) return {};
        return JSON.parse(storage);
    }

    // ========== Renderização dos cards a partir do localStorage ==========
    function renderizarCards(investimentosDoServidor = null) {
        const container = document.querySelector('.investimentos-lista');
        if (!container) return;

        let investimentos;
        if (investimentosDoServidor) {
            investimentos = {};
            investimentosDoServidor.forEach(item => {
                if (item.temporario) {
                    investimentos[item.id] = {
                        id: item.id,
                        investimentoId: item.investimento_id,
                        nome: item.nome,
                        quantidade: item.quantidade,
                        saldo: item.saldo,
                        lucroPrejuizo: item.lucro_prejuizo,
                        tempo_restante: item.tempo_restante,
                        tempo_inicio: item.tempo_inicio,
                        duracao: item.duracao,
                        temporario: true
                    };
                }
            });
            localStorage.setItem('investimentos_temporarios', JSON.stringify(investimentos));
        } else {
            investimentos = carregarInvestimentosDoStorage();
        }

        container.innerHTML = '';
        if (Object.keys(investimentos).length === 0) {
            container.innerHTML = '<div class="empty-state"><h3>Você ainda não tem investimentos</h3><p>Acesse a aba "Investir Agora" para começar.</p></div>';
            return;
        }

        for (const id in investimentos) {
            const inv = investimentos[id];
            const card = document.createElement('div');
            card.className = 'invest-item-card';
            card.dataset.id = inv.id;
            card.dataset.investimentoId = inv.investimentoId;
            card.dataset.temporario = '1';
            card.dataset.quantidade = inv.quantidade;
            card.dataset.saldo = inv.saldo;
            card.dataset.expira = inv.expira_em;
            card.innerHTML = `
                <div class="item-info"><strong>${inv.nome}</strong></div>
                <div class="item-details" style="display: flex; gap: 20px; flex-wrap: wrap;">
                    <div><small>Qtd:</small> <strong class="card-qtd">${inv.quantidade}</strong></div>
                    <div><small>Saldo:</small> <strong class="card-saldo">${formatBRL(inv.saldo)}</strong></div>
                    <div><small>Lucro/Prejuízo:</small> <strong class="card-lucro">${formatBRL(inv.lucroPrejuizo)}</strong></div>
                    <div><small>Tempo restante:</small> <strong class="tempo-restante">--</strong></div>
                </div>
                ${inv.temporario ? `
                <div class="progress-bar-container">
                    <div class="progress-bar-fill" style="width: 0%;"></div>
                </div>
                ` : ''}
            `;
            container.appendChild(card);
        }
    }

    // ========== Atualização dos cards com dados do servidor ==========
    function atualizarCardsComDadosDoServidor(carteira) {
        salvarInvestimentosNoStorage(carteira);
        const investimentosStorage = carregarInvestimentosDoStorage();
        document.querySelectorAll('.invest-item-card').forEach(card => {
            const uniqueId = card.dataset.id;
            if (!uniqueId) return;
            const inv = investimentosStorage[uniqueId];
            if (!inv) {
                card.remove();
                return;
            }
            const qtdEl = card.querySelector('.card-qtd');
            const saldoEl = card.querySelector('.card-saldo');
            const lucroEl = card.querySelector('.card-lucro');
            if (qtdEl) qtdEl.textContent = inv.quantidade;
            if (saldoEl) saldoEl.innerText = formatBRL(inv.saldo);
            if (lucroEl) {
                const lucroValor = inv.lucroPrejuizo;
                lucroEl.innerText = formatBRL(lucroValor);
                lucroEl.classList.remove('positive', 'negative');
                if (lucroValor > 0) {
                    lucroEl.classList.add('positive');
                } else if (lucroValor < 0) {
                    lucroEl.classList.add('negative');
                }
            }
            card.dataset.expira = inv.expira_em;
        });
    }

    function iniciarContagemLocal() {
        let animationId = null;
        let isRunning = true;

        // Função de animação contínua (chamada a cada frame)
        function atualizarBarrasContinuamente() {
            if (!isRunning) return;

            const investimentosStorage = carregarInvestimentosDoStorage();
            const agora = Date.now();

            for (const id in investimentosStorage) {
                const inv = investimentosStorage[id];
                const card = document.querySelector(`.invest-item-card[data-id="${id}"]`);
                if (!card) continue;

                const barraFill = card.querySelector('.progress-bar-fill');
                if (barraFill) {
                    const tempoRestanteMs = inv.duracao - (agora - inv.tempo_inicio);
                    if (tempoRestanteMs <= 0) {
                        // Investimento expirado será removido no próximo intervalo de texto
                        continue;
                    }
                    const tempoDecorridoMs = inv.duracao - tempoRestanteMs;
                    const percentual = (tempoDecorridoMs / inv.duracao) * 100;
                    barraFill.style.width = `${Math.min(100, Math.max(0, percentual))}%`;
                }
            }

            animationId = requestAnimationFrame(atualizarBarrasContinuamente);
        }

        // Atualização do texto de tempo restante a cada segundo
        setInterval(() => {
            const investimentosStorage = carregarInvestimentosDoStorage();
            const agora = Date.now();

            for (const id in investimentosStorage) {
                const inv = investimentosStorage[id];
                const card = document.querySelector(`.invest-item-card[data-id="${id}"]`);
                if (!card) continue;

                const tempoSpan = card.querySelector('.tempo-restante');
                if (tempoSpan) {
                    const tempoRestanteMs = inv.duracao - (agora - inv.tempo_inicio);
                    if (tempoRestanteMs <= 0) {
                        delete investimentosStorage[id];
                        card.remove();
                    } else {
                        const segundos = Math.floor(tempoRestanteMs / 1000);
                        const horas = Math.floor(segundos / 3600);
                        const minutos = Math.floor((segundos % 3600) / 60);
                        const segs = segundos % 60;
                        const texto = horas > 0
                            ? `${horas.toString().padStart(2, '0')}:${minutos.toString().padStart(2, '0')}:${segs.toString().padStart(2, '0')}`
                            : `${minutos.toString().padStart(2, '0')}:${segs.toString().padStart(2, '0')}`;
                        tempoSpan.textContent = texto;
                    }
                }
            }
        }, 1000);

        // Inicia a animação
        animationId = requestAnimationFrame(atualizarBarrasContinuamente);
    }
    // ========== Gráfico ==========
    const carregarHistorico = async (investimentoId) => {
        try {
            const res = await fetch(`/investimento/historico/${investimentoId}`, { headers: { 'Accept': 'application/json' } });
            if (!res.ok) return null;
            return await res.json();
        } catch {
            return null;
        }
    };

    const renderizarGrafico = (historico) => {
        if (!modalHistoricoCanvas) return;
        if (modalHistoricoChartInstance) modalHistoricoChartInstance.destroy();

        let pontos = Array.isArray(historico) ? [...historico] : [];
        pontos.sort((a, b) => new Date(a.data) - new Date(b.data));
        if (pontos.length > 60) pontos = pontos.slice(-60);

        const pontoAtual = { data: new Date().toISOString(), preco: currentPreco };
        const ultimoPonto = pontos[pontos.length - 1];
        const jaTemAtual = ultimoPonto && new Date(ultimoPonto.data).toISOString().slice(0, 19) === pontoAtual.data.slice(0, 19);

        if (!jaTemAtual) {
            pontos.push(pontoAtual);
            if (pontos.length > 60) pontos.shift();
        }

        const labels = pontos.map(p => formatarDataParaExibicao(p.data));
        const dados = pontos.map(p => Number(p.preco) || 0);

        let lineColor = '#0DA694';
        if (dados.length >= 2) {
            lineColor = dados[dados.length - 1] < dados[dados.length - 2] ? '#ef4444' : '#22c55e';
        }
        const lineBg = lineColor === '#ef4444' ? 'rgba(239, 68, 68, 0.15)' : 'rgba(34, 197, 94, 0.15)';

        modalHistoricoChartInstance = new Chart(modalHistoricoCanvas.getContext('2d'), {
            type: 'line',
            data: {
                labels,
                datasets: [{
                    label: 'Preço da cota',
                    data: dados,
                    borderColor: lineColor,
                    backgroundColor: lineBg,
                    pointRadius: 2,
                    borderWidth: 2,
                    tension: 0.25,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { ticks: { maxTicksLimit: 6 } },
                    y: { beginAtZero: false }
                }
            }
        });
    };

    const adicionarPontoAoGrafico = (novoPreco) => {
        if (!modalHistoricoChartInstance) return;
        const chart = modalHistoricoChartInstance;
        const novoLabel = formatarDataParaExibicao(new Date().toISOString());

        chart.data.labels.push(novoLabel);
        chart.data.datasets[0].data.push(novoPreco);

        if (chart.data.labels.length > 60) { 
            chart.data.labels.shift();
            chart.data.datasets[0].data.shift();
        }

        const dados = chart.data.datasets[0].data;
        if (dados.length >= 2) {
            const lineColor = dados[dados.length - 1] < dados[dados.length - 2] ? '#ef4444' : '#22c55e';
            const lineBg = lineColor === '#ef4444' ? 'rgba(239, 68, 68, 0.15)' : 'rgba(34, 197, 94, 0.15)';
            chart.data.datasets[0].borderColor = lineColor;
            chart.data.datasets[0].backgroundColor = lineBg;
        }
        chart.update();
    };

    const carregarErenderizarGrafico = async () => {
        if (!currentInvestimentoId) return;
        const historico = await carregarHistorico(currentInvestimentoId);
        if (historico) renderizarGrafico(historico);
    };

    // ========== Forms ==========
    const updateBuyTotal = () => {
        let qtd = parseFloat(inputQuantidadeComprar.value);
        if (isNaN(qtd) || qtd < 0) {
            qtd = 0;
            // Não reescreve o campo aqui
        }
        modalTotalCompraEl.innerText = formatBRL(currentPreco * qtd);
    };

    // ========== Modal ==========
    const carregarDetalhesModal = async (params) => {
        const { id, investimentoId, temporario } = params;
        currentUniqueId = id;
        currentInvestimentoId = investimentoId;
        modalTitulo.innerText = 'Carregando...';
        modalInfo.innerText = '...';
        modalPrecoCota.innerText = formatBRL(0);
        modalTotalCompraEl.innerText = formatBRL(0);
        currentPreco = 0;
        currentQuantidadeCarteira = null;
        inputInvestimentoIdComprar.value = investimentoId;
        inputQuantidadeComprar.value = ''; 
        let url;
        if (temporario !== undefined) {
            url = `/investimento/detalhes-item?tipo=${temporario ? 'temporario' : 'normal'}&id=${id}&investimento_id=${investimentoId}`;
        } else {
            url = `/investimento/detalhes/${investimentoId}`;
        }
        try {
            const res = await fetch(url, { headers: { 'Accept': 'application/json' } });
            if (!res.ok) throw new Error('Falha ao carregar dados do investimento.');
            const data = await res.json();
            currentPreco = Number(data.preco_atual) || 0;
            modalTitulo.innerText = data.nome || 'Investimento';
            modalInfo.innerText = data.descricao || 'Nenhuma descrição disponível.';
            modalPrecoCota.innerText = formatBRL(currentPreco);
            modalValorCarteiraEl.innerText = formatBRL(data.valor_carteira_total || 0);
            modalSaldoContaEl.innerText = formatBRL(data.saldo_conta || 0);
            if (data.risco) {
                modalRisco.style.display = 'inline-block';
                modalRisco.innerText = `Risco: ${data.risco}`;
                aplicarCoresRisco(data.risco);
            } else {
                modalRisco.style.display = 'none';
            }
            updateBuyTotal();
            if (data.tipo === 'carteira') {
                const qtd = parsePositiveInt(data.quantidade, 0);
                currentQuantidadeCarteira = qtd;
                modalCarteiraExtra.style.display = 'block';
                modalQtdCarteiraEl.innerText = String(qtd);
                if (typeof data.lucro_prejuizo !== 'undefined') {
                    modalLucroPrejuizoEl.innerText = formatBRL(data.lucro_prejuizo);
                }
            } else {
                modalCarteiraExtra.style.display = 'none';
                currentQuantidadeCarteira = null;
            }
            await carregarErenderizarGrafico();
        } catch (err) {
            modalTitulo.innerText = 'Erro';
            modalInfo.innerText = err.message || 'Não foi possível abrir o modal.';
        }
    };

    // ========== Polling ==========
    const atualizarValoresPagina = async () => {
        if (!saldoAtualEl) return;
        try {
            const res = await fetch('/investimento/atualizar-precos', { headers: { 'Accept': 'application/json' } });
            if (!res.ok) return;
            const data = await res.json();
            ultimoServerTime = data.server_time;
            ultimoLocalTime = Date.now();
            saldoAtualEl.innerText = formatBRL(data.saldo || 0);
            atualizarCardsComDadosDoServidor(data.carteira);
            
            const ativos = Array.isArray(data.ativos_disponiveis) ? data.ativos_disponiveis : [];
            const ativosPorId = new Map(ativos.map(item => [String(item.id), item]));
            
            document.querySelectorAll('.ativo-card').forEach(card => {
                const ativoId = card.dataset.ativoId;
                if (!ativoId) return;
                const ativo = ativosPorId.get(ativoId);
                if (!ativo) return;
                const precoEl = card.querySelector('.ativo-preco');
                if (precoEl) {
                    const precoAnterior = ultimosPrecos.get(ativoId) || parseFloat(card.dataset.preco || 0);
                    const precoNovo = ativo.valor_cota || 0;
                    precoEl.innerText = formatBRL(precoNovo);
                    card.dataset.preco = String(precoNovo);
                    
                    // Remove as classes antes de aplicar a nova direção
                    if (precoNovo > precoAnterior) {
                        precoEl.classList.remove('price-down');
                        precoEl.classList.add('price-up');
                    } else if (precoNovo < precoAnterior) {
                        precoEl.classList.remove('price-up');
                        precoEl.classList.add('price-down');
                    }
                    // Se precoNovo == precoAnterior, mantém a classe atual
                    ultimosPrecos.set(ativoId, precoNovo);
                }
                card.dataset.risco = String(ativo.risco || '');
            });
                    
            if (modal.classList.contains('active')) {
                let precoAtualizado = null;
                let qtdAtualizada = null;
                let lucroPrejuizo = null;
                
                // 1. Tenta encontrar na carteira (se currentUniqueId existe)
                if (currentUniqueId) {
                    const itemCarteira = data.carteira.find(item => item.id == currentUniqueId);
                    if (itemCarteira) {
                        precoAtualizado = Number(itemCarteira.preco_atual) || 0;
                        qtdAtualizada = Number(itemCarteira.quantidade) || 0;
                        lucroPrejuizo = itemCarteira.lucro_prejuizo;
                    }
                }
                
                // 2. Se não encontrou na carteira, tenta nos ativos disponíveis (pelo investimentoId)
                if (precoAtualizado === null && currentInvestimentoId) {
                    const ativo = data.ativos_disponiveis.find(a => a.id == currentInvestimentoId);
                    if (ativo) {
                        precoAtualizado = Number(ativo.valor_cota) || 0;
                    }
                }
                
                // Se encontrou algum preço, atualiza o modal e o gráfico
                if (precoAtualizado !== null) {
                    // Atualiza o preço atual se ele mudou
                    if (precoAtualizado !== currentPreco) {
                        const precoAnterior = currentPreco;
                        currentPreco = precoAtualizado;
                        modalPrecoCota.innerText = formatBRL(currentPreco);
                        updateBuyTotal();
                        
                        // Remove timer anterior, se existir
                        if (modalPriceTimeout) clearTimeout(modalPriceTimeout);
                        
                    // Aplica a classe permanentemente
                        if (precoAtualizado > precoAnterior) {
                            modalPrecoCota.classList.remove('price-down');
                            modalPrecoCota.classList.add('price-up');
                        } else if (precoAtualizado < precoAnterior) {
                            modalPrecoCota.classList.remove('price-up');
                            modalPrecoCota.classList.add('price-down');
                        }
                    }
                    
                    // SEMPRE adiciona um ponto no gráfico com o preço atual
                    adicionarPontoAoGrafico(currentPreco);
                    
                    // Atualiza quantidade e lucro/prejuízo se existirem
                    if (qtdAtualizada !== null && qtdAtualizada !== currentQuantidadeCarteira) {
                        currentQuantidadeCarteira = qtdAtualizada;
                        modalQtdCarteiraEl.innerText = String(currentQuantidadeCarteira);
                    }
                    if (lucroPrejuizo !== null && lucroPrejuizo !== undefined) {
                        modalLucroPrejuizoEl.innerText = formatBRL(lucroPrejuizo);
                    }
                } else {
                    // Caso o ativo não seja encontrado nem na carteira nem nos disponíveis (ex: foi removido)
                    // Se for um item temporário e não estiver mais no storage, fecha o modal
                    if (currentUniqueId) {
                        const investimentosStorage = carregarInvestimentosDoStorage();
                        if (!investimentosStorage[currentUniqueId]) {
                            modal.classList.remove('active');
                        }
                    }
                }
            }
            
            if (data.notificacoes && data.notificacoes.length > 0) {
                data.notificacoes.forEach(notif => {
                    if (notif.tipo === 'venda_automatica') {
                        const lucro = notif.lucro;
                        const lucroFormatado = formatBRL(lucro);
                        const mensagem = `${notif.quantidade} cota(s) do ativo ${notif.nome} foi vendida automaticamente. ${lucro >= 0 ? 'Lucro:' : 'Prejuízo:'} ${lucroFormatado}`;
                        const tipo = lucro >= 0 ? 'success' : 'error';
                        if (typeof showPopup === 'function') showPopup(mensagem, tipo);
                    } else {
                        if (typeof showPopup === 'function') showPopup(notif, 'info');
                    }
                });
            }
        } catch (err) {
            console.warn('Erro no polling de atualização:', err);
        }
    };

    // ========== Abrir modal ==========
    const abrirModalPeloCard = async (e, card) => {
        console.log("Abrindo modal para card:", card);
        if (e && (e.target.closest('form') || e.target.closest('button'))) return;
        const investimentoId = card.dataset.investimentoId || card.dataset.ativoId;
        if (!investimentoId) return;
        console.log("investimentoId:", investimentoId);
        const uniqueId = card.dataset.id;
        const temporario = card.dataset.temporario === '1';
        if (uniqueId !== undefined) {
            await carregarDetalhesModal({ id: uniqueId, investimentoId, temporario });
        } else {
            await carregarDetalhesModal({ investimentoId });
        }
        modal.classList.add('active');
    };
    
    // ========== Event Listeners ==========
    formComprar.addEventListener('submit', function(e) {
        let qtdStr = inputQuantidadeComprar.value.trim();
        
        // Substitui vírgula por ponto (se houver)
        qtdStr = qtdStr.replace(',', '.');
        
        let qtd = parseFloat(qtdStr);
        
        // Valida: não pode ser vazio, NaN, zero ou negativo
        if (qtdStr === '' || isNaN(qtd) || qtd <= 0) {
            e.preventDefault();
            if (typeof showPopup === 'function') {
                showPopup('Por favor, insira uma quantidade válida (maior que zero).', 'error');
            }
            return false;
        }
        
        // Garante que o valor enviado seja com ponto decimal
        inputQuantidadeComprar.value = qtd;
        return true;
    });
    // No DOMContentLoaded, após obter inputQuantidadeComprar
    if (inputQuantidadeComprar) {
        // Apenas atualiza o total quando o valor mudar (não modifica o campo)
        inputQuantidadeComprar.addEventListener('input', function() {
            updateBuyTotal();
        });

        // No blur, garante que o valor seja um número válido (corrige vazio ou NaN)
        inputQuantidadeComprar.addEventListener('blur', function() {
            let val = this.value;
            if (val === '' || val === null) {
                this.value = '0';
            } else {
                let num = parseFloat(val);
                if (isNaN(num)) {
                    this.value = '0';
                } else {
                    this.value = num;
                }
            }
            updateBuyTotal();
        });
}
    btnClose.addEventListener('click', () => modal.classList.remove('active'));
    // modal.addEventListener('click', (e) => { if (e.target === modal) modal.classList.remove('active'); });

    const containerCarteira = document.querySelector('.investimentos-lista');
    if (containerCarteira) {
        containerCarteira.addEventListener('click', (e) => {
            const card = e.target.closest('.invest-item-card');
            if (!card) return;
            if (e.target.closest('form') || e.target.closest('button')) return;
            abrirModalPeloCard(e, card);
        });
    }

    const containersAtivos = document.querySelectorAll('.ativos-grid');

    containersAtivos.forEach(container => {
        container.addEventListener('click', (e) => {
            const card = e.target.closest('.ativo-card');
            if (!card) return;
            if (e.target.closest('form') || e.target.closest('button')) return;
            abrirModalPeloCard(e, card);
        });
    });

    // ========== Inicialização ==========
    renderizarCards(window.initialCarteira);
    iniciarContagemLocal();
    atualizarValoresPagina().catch(() => {});
    setInterval(() => atualizarValoresPagina().catch(() => {}), 5000);
});