// ============================================
// CARROSSEL SIMPLES (APENAS IMAGENS)
// ============================================
const container = document.getElementById('adsGrid');
const indicatorsContainer = document.getElementById('carouselIndicators');
const items = container.children;
let autoScrollTimeout;
let isHovering = false;
let currentSlideIndex = 0;

// ========== FUNÇÕES DO CARROSSEL ==========
function createIndicators() {
    if (!indicatorsContainer) return;
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
    if (!indicatorsContainer) return;
    const index = Math.round(container.scrollLeft / container.offsetWidth);
    const dots = document.querySelectorAll('.indicator');
    dots.forEach((dot, i) => dot.classList.toggle('active', i === index));
    currentSlideIndex = index;
}

function scrollToSlide(index) {
    if (index < 0) index = 0;
    if (index >= items.length) index = 0;
    container.scrollTo({ left: index * container.offsetWidth, behavior: 'smooth' });
}

window.sideScroll = function(direction) {
    let newIndex = currentSlideIndex;
    if (direction === 'left') {
        newIndex = currentSlideIndex - 1;
        if (newIndex < 0) newIndex = items.length - 1;
    } else {
        newIndex = currentSlideIndex + 1;
        if (newIndex >= items.length) newIndex = 0;
    }
    scrollToSlide(newIndex);
    resetAutoScroll();
};

function resetAutoScroll() {
    clearTimeout(autoScrollTimeout);
    autoScrollTimeout = setTimeout(() => {
        if (!isHovering) sideScroll('right');
    }, 5000);
}

// ========== EVENTOS ==========
container.addEventListener('scroll', () => {
    clearTimeout(window.scrollFinished);
    window.scrollFinished = setTimeout(() => {
        updateIndicators();
    }, 150);
});

container.addEventListener('mouseenter', () => {
    isHovering = true;
    clearTimeout(autoScrollTimeout);
});

container.addEventListener('mouseleave', () => {
    isHovering = false;
    resetAutoScroll();
});

// ========== INICIALIZAÇÃO ==========
createIndicators();
updateIndicators();
resetAutoScroll();