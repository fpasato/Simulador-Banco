// 🔥 ATUALIZAR SALDO CONSTANTEMENTE - ESPECÍFICO PARA PIX
async function carregarSaldo() {
    try {
        const res = await fetch("/home/get-saldo");
        const data = await res.json();
        
        if (data.saldo !== undefined) {
            
            // Atualiza todos os elementos que mostram saldo
            const elementos = document.querySelectorAll('[data-saldo]');

            
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
        console.error("Erro ao carregar saldo PIX:", error);
    }
}

// Carrega ao abrir a página
document.addEventListener('DOMContentLoaded', carregarSaldo);

// Atualiza a cada 5 segundos
setInterval(carregarSaldo, 5000);



  async function generateKey() {
        try {
            const response = await fetch("/pix/generate_random_key", {
                method: "POST"
            });

            const data = await response.json();

            if (data.success) {
                // coloca chave no input
                document.querySelector("input[name='chave']").value = data.chave;

                // habilita botão
                document.getElementById("btn-confirmar").disabled = false;
            } else {
                alert("Erro ao gerar chave");
            }

        } catch (error) {
            console.error(error);
            alert("Erro na requisição");
        }
    }
    
    function formatarMoeda(input) {
        let valor = input.value.replace(/\D/g, '');
        
        if (valor === '') {
            document.getElementById('valor_real_pix').value = '';
            return;
        }
        
        // Converte para centavos e formata
        valor = parseInt(valor) / 100;
        valor = valor.toFixed(2).replace('.', ',');
        valor = valor.replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1.');
        
        input.value = valor;
        
        // Atualiza campo hidden com valor numérico (substitui vírgula por ponto)
        document.getElementById('valor_real_pix').value = valor.replace(/\./g, '').replace(',', '.');
    }