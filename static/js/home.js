
  const container = document.getElementById('adsGrid');
  const indicatorsContainer = document.getElementById('carouselIndicators');
  const video = document.getElementById('adVideo');
  const video2 = document.getElementById('adVideo2');
  const soundBtn = document.getElementById('soundBtn');
  const soundBtn2 = document.getElementById('soundBtn2');
  const items = container.children;
  let autoScrollTimeout; // Mudamos de Interval para Timeout para controle dinâmico
  let isHovering = false;

  // IMPORTANTE: Remover o atributo 'loop' dos vídeos no HTML para o evento 'ended' funcionar
  if (video) video.loop = false;
  if (video2) video2.loop = false;

  // Controle de Som - Primeiro vídeo
  if (video && soundBtn) {
    const toggleMute = () => {
      video.muted = !video.muted;
      soundBtn.innerHTML = video.muted ? '🔇' : '🔊';
    };
    soundBtn.addEventListener('click', (e) => { e.stopPropagation(); toggleMute(); });
    video.addEventListener('click', toggleMute);
  }

  // Controle de Som - Segundo vídeo
  if (video2 && soundBtn2) {
    const toggleMute2 = () => {
      video2.muted = !video2.muted;
      soundBtn2.innerHTML = video2.muted ? '🔇' : '🔊';
    };
    soundBtn2.addEventListener('click', (e) => { e.stopPropagation(); toggleMute2(); });
    video2.addEventListener('click', toggleMute2);
  }

  // Indicadores
  function createIndicators() {
    indicatorsContainer.innerHTML = '';
    for (let i = 0; i < items.length; i++) {
      const dot = document.createElement('div');
      dot.className = 'indicator' + (i === 0 ? ' active' : '');
      dot.addEventListener('click', () => {
        container.scrollTo({ left: i * container.offsetWidth, behavior: 'smooth' });
        resetAutoScroll();
      });
      indicatorsContainer.appendChild(dot);
    }
  }

  function updateIndicators() {
    const index = Math.round(container.scrollLeft / container.offsetWidth);
    const dots = document.querySelectorAll('.indicator');
    dots.forEach((dot, i) => dot.classList.toggle('active', i === index));
    
    // Se mudou de slide (via scroll manual ou botão), recalcula o tempo
    resetAutoScroll();
  }

  window.sideScroll = function(direction) {
    const step = container.offsetWidth;
    if (direction === 'left') {
      container.scrollBy({ left: -step, behavior: 'smooth' });
    } else {
      const isAtEnd = container.scrollLeft + step >= container.scrollWidth - 10;
      if (isAtEnd) container.scrollTo({ left: 0, behavior: 'smooth' });
      else container.scrollBy({ left: step, behavior: 'smooth' });
    }
    resetAutoScroll();
  };

  // --- NOVA LÓGICA DE TEMPO ---
  function manageAutoRotation() {
    if (isHovering) return;

    const index = Math.round(container.scrollLeft / container.offsetWidth);
    const currentItem = items[index];

    // Verifica se o slide atual contém o primeiro vídeo
    if (currentItem && currentItem.contains(video)) {
      video.play();
      // Não criamos um Timeout aqui. O vídeo chamará o próximo slide ao terminar.
      video.onended = () => {
        if (!video.muted) { // se o vídeo não estiver mutado
          video.muted = true;  // muta o vídeo
        }
        window.sideScroll('right'); // passa para o próximo slide
      };
    } 
    // Verifica se o slide atual contém o segundo vídeo
    else if (currentItem && currentItem.contains(video2)) {
      video2.play();
      // Não criamos um Timeout aqui. O vídeo chamará o próximo slide ao terminar.
      video2.onended = () => {
        if (!video2.muted) { // se o vídeo não estiver mutado
          video2.muted = true;  // muta o vídeo
        }
        window.sideScroll('right'); // passa para o próximo slide
      };
    } 
    else {
      // Se for imagem, passa em 5 segundos
      autoScrollTimeout = setTimeout(() => {
        window.sideScroll('right');
      }, 5000);
    }
  }

  function resetAutoScroll() {
    clearTimeout(autoScrollTimeout);
    if (video) video.onended = null; // Limpa o evento do primeiro vídeo
    if (video2) video2.onended = null; // Limpa o evento do segundo vídeo
    manageAutoRotation();
  }

  container.addEventListener('scroll', () => {
    // Usamos um pequeno debounce para não disparar 1000x durante o scroll
    clearTimeout(window.scrollFinished);
    window.scrollFinished = setTimeout(updateIndicators, 150);
  });

  container.addEventListener('mouseenter', () => { 
    isHovering = true; 
    clearTimeout(autoScrollTimeout);
  });
  
  container.addEventListener('mouseleave', () => { 
    isHovering = false; 
    manageAutoRotation();
  });

  createIndicators();
  manageAutoRotation(); // Inicia o ciclo


// 🔥 CARREGAR SALARIO AO CARREGAR PÁGINA
async function carregarSaldoInicial() {
    try {
        const res = await fetch("/home/get-saldo");
        const data = await res.json();
        
        if (data.saldo !== undefined) {
            console.log("Saldo inicial carregado:", data.saldo);
            
            // Atualiza todos os elementos que mostram saldo
            const elementos = document.querySelectorAll('[data-saldo]');
            elementos.forEach(el => {
                if (el) {
                    el.textContent = `R$ ${parseFloat(data.saldo).toFixed(2)}`;
                }
            });
        }
    } catch (error) {
        console.error("Erro ao carregar saldo:", error);
    }
}

async function verificarSalario() {
    const res = await fetch("/home/verificar-salario");
    const data = await res.json();

    console.log("verificando...", data); // DEBUG

    if (data.novo) {
        showPopup(`Salário de R$${data.valor.toFixed(2)} foi creditado`, "success");
        
        // 🔥 RECARRREGA SALARIO NA SESSÃO
        await fetch("/home/recarregar-saldo")
            .then(res => res.json())
            .then(data => {
                if (data.saldo !== undefined) {
                    console.log("Saldo recarregado:", data.saldo);
                    // Atualiza o saldo na tela (se tiver elemento)
                    const saldoElement = document.querySelector('[data-saldo]');
                    if (saldoElement) {
                        saldoElement.textContent = `R$ ${parseFloat(data.saldo).toFixed(2)}`;
                    }
                }
            });
    }
}

verificarSalario(); // 🔥 ESSENCIAL - chama na primeira vez
setInterval(verificarSalario, 5000); // a cada 5 segundos
