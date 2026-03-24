(function() {
    function setThemeIcon(theme) {
        const themeIcon = document.querySelector('#theme-toggle img');
        if (!themeIcon) return;
        const iconPath = theme === 'dark' 
            ? '/static/icons/theme_icons/sun.png'
            : '/static/icons/theme_icons/moon.png';
        themeIcon.src = iconPath;
    }

    function applyTheme(theme) {
        document.body.classList.remove('lighttheme', 'darktheme');
        document.body.classList.add(`${theme}theme`);
        setThemeIcon(theme);
        localStorage.setItem('theme', theme);
    }

    // Carrega o tema salvo (garantindo que a classe já está aplicada pelo script inline)
    const savedTheme = localStorage.getItem('theme') || 'light';
    // Sincroniza o ícone (a classe já está no body, mas o ícone pode estar errado)
    setThemeIcon(savedTheme);

    // Configura o evento de clique
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const isLight = document.body.classList.contains('lighttheme');
            const newTheme = isLight ? 'dark' : 'light';
            applyTheme(newTheme);
        });
    }
})();