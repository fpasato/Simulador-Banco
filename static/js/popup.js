function showPopup(message, type = 'success', title = '') {
  const popup = document.getElementById('popup');
  const titleEl = document.getElementById('popup-title');
  const textEl = document.getElementById('popup-text');

  titleEl.innerText = title || (type === 'success' ? 'Sucesso!' : 'Ops!');
  textEl.innerText = message;

  // Reseta classes e aplica a nova
  popup.className = `popup show ${type}`;

  // Auto-hide após 5 segundos
  setTimeout(() => {
    closePopup();
  }, 5000);
}

function closePopup() {
    const popup = document.getElementById('popup');
    
    // Adiciona a classe que dispara o slide lateral
    popup.classList.add('hide');

    // Espera 600ms (tempo da animação CSS) para resetar o estado
    setTimeout(() => {
        popup.classList.remove('show', 'hide');
    }, 600); 
}

