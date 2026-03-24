// 1. Aplicar estilos conforme as diretrizes Lumo Blue
function aplicarEstilosFaturas() {
    document.querySelectorAll('.fatura-container table tbody tr').forEach(row => {
        const statusCell = row.children[2]; // Status (3ª coluna)
        const valueCell = row.children[1];  // Valor (2ª coluna)
        const jurosCell = row.children[4];  // Juros (5ª coluna)
        
        // --- Status ---
        if (statusCell) {
            statusCell.className = ''; 
            const status = statusCell.textContent.toLowerCase();

            if (status.includes('pendente')) statusCell.classList.add('status-pendente');
            else if (status.includes('pago')) statusCell.classList.add('status-pago');
            else if (status.includes('atrasado')) statusCell.classList.add('status-atrasado');
        }
        
        // --- Valor ---
        if (valueCell) {
            valueCell.className = '';
            const valueText = valueCell.textContent.trim();
            const value = parseFloat(valueText.replace('R$', '').replace('.', '').replace(',', '.'));
            
            if (!isNaN(value)) {
                if (value > 1000) valueCell.classList.add('valor-alto');
                else if (value > 500) valueCell.classList.add('valor-medio');
                else valueCell.classList.add('valor-baixo');
            }
        }
        
        // --- Juros ---
        if (jurosCell) {
            jurosCell.className = '';
            const jurosText = jurosCell.textContent.trim();
            const juros = parseFloat(jurosText.replace('%', ''));
            
            if (!isNaN(juros)) {
                if (juros > 10) jurosCell.classList.add('juros-alto');
                else if (juros > 0) jurosCell.classList.add('juros-medio');
                else jurosCell.classList.add('juros-zero');
            }
        }
    });
}

// Executa assim que a página carregar
document.addEventListener('DOMContentLoaded', () => {
    aplicarEstilosFaturas();
});

// Captura todos os formulários de fatura (menos o botão "Pagar Todas")
document.querySelectorAll('form[action="/faturas/pagar"]').forEach(form => {
    form.addEventListener('submit', function(e) {
        e.preventDefault(); // Impede o navegador de abrir a tela branca com o JSON

        const formData = new FormData(this);
        const botao = this.querySelector('button');
        botao.disabled = true; // Evita cliques duplos

        fetch('/faturas/pagar', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // 1. Atualiza o saldo na tela
                const saldoCard = document.querySelector('.saldo-card span');
                if (saldoCard) {
                    saldoCard.textContent = `Saldo Disponível: R$ ${data.novo_saldo.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
                }

                // 2. Remove a linha da fatura que foi paga
                this.closest('.fatura-container').remove();

                // 3. EXIBE O POPUP HTML
                showPopup("Sua fatura foi paga e o saldo atualizado!", 'success', 'Pagamento Concluído');

                // 4. Se não houver mais faturas, atualiza o título
                if (document.querySelectorAll('.fatura-container').length === 1) {
                    const faturasList = document.querySelector('.faturas-list');
                    faturasList.innerHTML = '<div class="fatura-container"><h2 class="fatura-title">Você não tem faturas pendentes</h2></div>';
                }
            } else {
                // Se quiser usar o popup para erro também:
                showPopup(data.error, 'error', 'Erro');
                botao.disabled = false;
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            botao.disabled = false;
        });
    });
});

// Adiciona evento específico para o botão "Pagar Todas"
document.querySelector('#btn-pagar-todas')?.addEventListener('click', function(e) {
    e.preventDefault();
    
    const botao = this;
    botao.disabled = true;
    botao.textContent = 'Processando...';
    
    fetch('/faturas/pagar-todas', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // 1. Atualiza o saldo na tela
            const saldoCard = document.querySelector('.saldo-card span');
            if (saldoCard) {
                saldoCard.textContent = `Saldo Disponível: R$ ${data.novo_saldo.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
            }
            
            // 2. Remove todas as faturas
            document.querySelectorAll('.fatura-container').forEach(container => {
                container.remove();
            });
            
            // 3. Mostra mensagem de sem faturas
            const faturasList = document.querySelector('.faturas-list');
            faturasList.innerHTML = '<div class="fatura-container"><h2 class="fatura-title">Você não tem faturas pendentes</h2></div>';
            
            // 4. Popup de sucesso
            showPopup(
                `${data.faturas_pagas} fatura(s) paga(s) no valor total de R$ ${data.valor_total.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`, 
                'success', 
                'Pagamento Concluído'
            );
            
        } else {
            showPopup(data.error, 'error', 'Erro');
        }
        
        // Restaura o botão
        botao.disabled = false;
        botao.textContent = 'Pagar Todas';
    })
    .catch(error => {
        console.error('Erro:', error);
        showPopup('Erro ao processar pagamento', 'error', 'Falha na Operação');
        botao.disabled = false;
        botao.textContent = 'Pagar Todas';
    });
});