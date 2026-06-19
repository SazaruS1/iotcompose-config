// ===================================
// Gestion de l'overlay
// ===================================

function showOverlay() {
    document.getElementById("myOverlay").classList.remove("d-none");
}

function hideOverlay() {
    document.getElementById("myOverlay").classList.add("d-none");
}

// ===================================
// Gestion de la reprise du Scroll
// ===================================

function saveScrollPosition() {
    // Sauvegarder la position verticale actuelle du scroll
    localStorage.setItem('scrollPosition', window.scrollY);
}

function restoreScrollPosition() {
    const scrollPosition = localStorage.getItem('scrollPosition');
    if (scrollPosition !== null) {
        window.scrollTo(0, parseInt(scrollPosition, 10));
        localStorage.removeItem('scrollPosition'); // Supprimer la valeur après utilisation pour ne pas la garder
    }
}

window.addEventListener('loaded', restoreScrollPosition);
//window.addEventListener('DOMContentLoaded', restoreScrollPosition);

// ===================================
// Effacement automatique des flashs
// ===================================

document.addEventListener("DOMContentLoaded", () => {
    const flashes = document.querySelectorAll(".flash-bubble");
    flashes.forEach(flash => {
        flash.addEventListener("animationend", (e) => {
            if (e.animationName === "fadeOut") {
                flash.remove();
            }
        });
    });
});



// ===================================
// Confirmation utilisateur
// ===================================
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.confirm').forEach(link => {
    link.addEventListener('click', event => {
      if (!confirm('Vraiment ??')) {
        event.preventDefault(); // bloque la navigation
      }
    });
  });
});