document.addEventListener('DOMContentLoaded', (event) => {
    console.log("Portal de Movilidad - Sitio Web Cargado");

    // --- Image Slider Logic ---
    // This is a basic setup. A real implementation would have multiple slides
    // and more complex logic for transitions, dots, arrows, etc.
    const slides = document.querySelectorAll('.slide');
    let currentSlide = 0;

    function showSlide(index) {
        slides.forEach((slide, i) => {
            slide.classList.remove('active');
            if (i === index) {
                slide.classList.add('active');
            }
        });
    }

    // In the future, you could add event listeners for next/prev buttons
    // e.g., document.querySelector('.next-btn').addEventListener('click', () => { ... });

    // For now, it just ensures the first slide is active.
    showSlide(currentSlide);
});
