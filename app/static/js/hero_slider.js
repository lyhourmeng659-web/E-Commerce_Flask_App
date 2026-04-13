/**
 * hero_slider.js — ShopHub
 * Handles the hero image slider: dot indicators, prev/next buttons, auto-advance, scroll sync.
 */

document.addEventListener('DOMContentLoaded', () => {

    const slider   = document.getElementById('heroSlider');
    const dotsWrap = document.getElementById('sliderDots');
    const prevBtn  = document.getElementById('sliderPrev');
    const nextBtn  = document.getElementById('sliderNext');

    // Only run on pages that have the slider
    if (!slider || !dotsWrap) return;

    const total = slider.children.length;
    let current = 0;
    let timer;

    //  Build dot indicators
    for (let i = 0; i < total; i++) {
        const btn = document.createElement('button');
        btn.className = 'dot-btn' + (i === 0 ? ' active' : '');
        btn.setAttribute('role', 'tab');
        btn.setAttribute('aria-label', 'Slide ' + (i + 1));
        btn.addEventListener('click', () => goTo(i));
        dotsWrap.appendChild(btn);
    }

    //  Navigate to a specific slide
    function goTo(n) {
        current = (n + total) % total;
        slider.scrollTo({ left: current * slider.offsetWidth, behavior: 'smooth' });
        updateDots();
        resetTimer();
    }

    //  Sync dot active state
    function updateDots() {
        [...dotsWrap.children].forEach((dot, i) => {
            dot.classList.toggle('active', i === current);
        });
    }

    //  Auto-advance every 5 s
    function resetTimer() {
        clearInterval(timer);
        timer = setInterval(() => goTo(current + 1), 5000);
    }

    //  Prev / Next buttons
    prevBtn?.addEventListener('click', () => goTo(current - 1));
    nextBtn?.addEventListener('click', () => goTo(current + 1));

    //  Sync dots when user swipes / scrolls manually
    slider.addEventListener('scroll', () => {
        const idx = Math.round(slider.scrollLeft / slider.offsetWidth);
        if (idx !== current) {
            current = idx;
            updateDots();
        }
    }, { passive: true });

    //  Kick off
    resetTimer();

});