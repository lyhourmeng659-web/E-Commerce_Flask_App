/**
 * main.js — ShopHub
 * All global UI scripts: header scroll, mobile drawer, toast auto-dismiss.
 */

document.addEventListener('DOMContentLoaded', () => {

    //  Header scroll shadow
    const header = document.getElementById('siteHeader');
    if (header) {
        window.addEventListener('scroll', () => {
            header.classList.toggle('scrolled', window.scrollY > 10);
        }, { passive: true });
    }

    //  Mobile drawer
    const overlay   = document.getElementById('mobileOverlay');
    const drawer    = document.getElementById('mobileDrawer');
    const toggleBtn = document.getElementById('mobileMenuToggle');
    const closeBtn  = document.getElementById('drawerCloseBtn');

    function openDrawer() {
        overlay?.classList.add('open');
        drawer?.classList.add('open');
        drawer?.setAttribute('aria-hidden', 'false');
        toggleBtn?.setAttribute('aria-expanded', 'true');
        document.body.style.overflow = 'hidden';
    }

    function closeDrawer() {
        overlay?.classList.remove('open');
        drawer?.classList.remove('open');
        drawer?.setAttribute('aria-hidden', 'true');
        toggleBtn?.setAttribute('aria-expanded', 'false');
        document.body.style.overflow = '';
    }

    toggleBtn?.addEventListener('click', openDrawer);
    closeBtn?.addEventListener('click', closeDrawer);
    overlay?.addEventListener('click', closeDrawer);
    document.addEventListener('keydown', e => {
        if (e.key === 'Escape') closeDrawer();
    });

    //  Toast auto-dismiss (5 s)
    document.querySelectorAll('.toast').forEach(toast => {
        setTimeout(() => {
            if (toast.isConnected) toast.remove();
        }, 5000);
    });

});