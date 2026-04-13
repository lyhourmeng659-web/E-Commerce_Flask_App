document.addEventListener('DOMContentLoaded', () => {

    const dec = document.getElementById('pd-qty-dec');
    const inc = document.getElementById('pd-qty-inc');
    const hidden = document.getElementById('pd-qty-val');
    const display = document.getElementById('pd-qty-display');

    // Only run on pages that have the stepper
    if (!dec || !inc || !hidden || !display) return;

    // Read max stock from data attribute set by Jinja in the HTML
    const max = parseInt(inc.dataset.max, 10) || 0;
    let qty = 1;

    function render() {
        display.textContent = qty;
        hidden.value = qty;
        dec.style.opacity = qty <= 1 ? '.35' : '1';
        inc.style.opacity = qty >= max ? '.35' : '1';
    }

    dec.addEventListener('click', () => {
        if (qty > 1) {
            qty--;
            render();
        }
    });
    inc.addEventListener('click', () => {
        if (qty < max) {
            qty++;
            render();
        }
    });

    render();

});
