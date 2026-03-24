
// 🔥 ATUALIZAR SALDO CONSTANTEMENTE - TRANSFERÊNCIA
async function carregarSaldo() {
    try {
        const res = await fetch("/home/get-saldo");
        const data = await res.json();
        
        if (data.saldo !== undefined) {
            console.log("Saldo Transferência atualizado:", data.saldo);
            
            // Atualiza todos os elementos que mostram saldo
            const elementos = document.querySelectorAll('[data-saldo]');
            console.log("Elementos encontrados:", elementos.length);
            
            elementos.forEach(el => {
                if (el) {
                    // Formatação segura com toLocaleString incluindo R$
                    const saldo = Number(data.saldo);
                    el.textContent = "R$ " + saldo.toLocaleString("pt-BR", {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                    });
                }
            });
        }
    } catch (error) {
        console.error("Erro ao carregar saldo Transferência:", error);
    }
}


// Carrega ao abrir a página
document.addEventListener('DOMContentLoaded', carregarSaldo);

// Atualiza a cada 5 segundos
setInterval(carregarSaldo, 5000);

console.log("Script Transferência carregado!");
