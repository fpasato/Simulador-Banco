// Usa as variáveis globais urlPagarFatura e urlPagarTodas

const searchInput = document.getElementById('search-input');
const statusBtns = document.querySelectorAll('.status-btn');
const cards = document.querySelectorAll('.fatura-card');
const pagarTodasBtn = document.getElementById('pagar-todas-btn');
const saldoSpan = document.getElementById('saldo-valor');
let activeStatus = 'all';

function showToast(message, isError = false) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.style.background = isError ? '#b91c1c' : '#10b981';
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3000);
}

function updateSaldo(novoSaldo) {
    if (saldoSpan) saldoSpan.textContent = `R$ ${novoSaldo.toFixed(2)}`;
}

function filterCards() {
    const searchTerm = searchInput.value.toLowerCase().trim();
    cards.forEach(card => {
        const tipo = card.getAttribute('data-tipo').toLowerCase();
        const descricao = card.getAttribute('data-descricao').toLowerCase();
        const valor = card.getAttribute('data-valor');
        const status = card.getAttribute('data-status');
        let matchesSearch = searchTerm === '' || tipo.includes(searchTerm) || descricao.includes(searchTerm) || valor.includes(searchTerm);
        let matchesStatus = activeStatus === 'all' || activeStatus === status;
        card.style.display = (matchesSearch && matchesStatus) ? '' : 'none';
    });
}

let debounceTimeout;
if (searchInput) {
    searchInput.addEventListener('input', () => {
        clearTimeout(debounceTimeout);
        debounceTimeout = setTimeout(filterCards, 300);
    });
}

statusBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        statusBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        activeStatus = btn.getAttribute('data-status');
        filterCards();
    });
});

async function pagarFatura(faturaId, cardElement) {
    const formData = new FormData();
    formData.append('fatura_id', faturaId);
    try {
        const response = await fetch(urlPagarFatura, { method: 'POST', body: formData });
        const data = await response.json();
        if (response.ok && data.success) {
            updateSaldo(data.novo_saldo);
            const statusSpan = cardElement.querySelector('.status');
            statusSpan.innerHTML = 'Pago';
            statusSpan.classList.remove('pendente');
            statusSpan.classList.add('pago');
            const btn = cardElement.querySelector('.btn-pagar');
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-check-circle"></i> Paga';
            btn.style.background = '#e2e8f0';
            btn.style.color = '#64748b';
            cardElement.setAttribute('data-status', 'pago');
            showToast('Fatura paga com sucesso!');
            filterCards();
        } else {
            showToast(data.error || 'Erro ao pagar fatura', true);
        }
    } catch (err) {
        console.error(err);
        showToast('Erro de conexão', true);
    }
}

async function pagarTodas() {
    try {
        const response = await fetch(urlPagarTodas, { method: 'POST', headers: { 'Content-Type': 'application/json' } });
        const data = await response.json();
        if (response.ok && data.success) {
            updateSaldo(data.novo_saldo);
            cards.forEach(card => {
                if (card.getAttribute('data-status') === 'pendente') {
                    const statusSpan = card.querySelector('.status');
                    statusSpan.innerHTML = 'Pago';
                    statusSpan.classList.remove('pendente');
                    statusSpan.classList.add('pago');
                    const btn = card.querySelector('.btn-pagar');
                    btn.disabled = true;
                    btn.innerHTML = '<i class="fas fa-check-circle"></i> Paga';
                    btn.style.background = '#e2e8f0';
                    btn.style.color = '#64748b';
                    card.setAttribute('data-status', 'pago');
                }
            });
            showToast(`${data.faturas_pagas} faturas pagas! Total: R$ ${data.valor_total.toFixed(2)}`);
            filterCards();
        } else {
            showToast(data.error || 'Erro ao pagar todas', true);
        }
    } catch (err) {
        console.error(err);
        showToast('Erro de conexão', true);
    }
}

document.querySelectorAll('.btn-pagar:not([disabled])').forEach(btn => {
    btn.addEventListener('click', (e) => {
        const faturaId = btn.getAttribute('data-id');
        const card = btn.closest('.fatura-card');
        if (faturaId && card) pagarFatura(faturaId, card);
    });
});

if (pagarTodasBtn) pagarTodasBtn.addEventListener('click', pagarTodas);