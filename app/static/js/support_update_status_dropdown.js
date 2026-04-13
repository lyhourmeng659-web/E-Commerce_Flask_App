document.addEventListener('DOMContentLoaded', () => {

    const trigger = document.getElementById('sup-status-trigger');
    const listbox = document.getElementById('sup-status-listbox');
    const select = document.getElementById('sup-status-select');
    const labelEl = document.getElementById('sup-status-label');
    const chevron = document.getElementById('sup-status-chevron');

    // Only run on pages that have the support status dropdown
    if (!trigger || !listbox) return;

    // Wrap in a relative container so the floating listbox positions correctly
    const wrapper = document.createElement('div');
    wrapper.style.position = 'relative';
    trigger.parentNode.insertBefore(wrapper, trigger);
    wrapper.appendChild(trigger);
    wrapper.appendChild(listbox);

    //  Open / Close
    function open() {
        listbox.style.display = 'block';
        trigger.style.borderColor = '#4F46E5';
        trigger.style.background = '#fff';
        trigger.style.boxShadow = '0 0 0 3px rgba(79,70,229,.1)';
        chevron.style.transform = 'rotate(180deg)';
        trigger.setAttribute('aria-expanded', 'true');
    }

    function close() {
        listbox.style.display = 'none';
        trigger.style.borderColor = '#E2E8F0';
        trigger.style.background = '#F8FAFC';
        trigger.style.boxShadow = 'none';
        chevron.style.transform = 'rotate(0deg)';
        trigger.setAttribute('aria-expanded', 'false');
    }

    //  Events
    trigger.addEventListener('click', () => {
        listbox.style.display === 'block' ? close() : open();
    });

    trigger.addEventListener('keydown', e => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            open();
        }
        if (e.key === 'Escape') close();
    });

    listbox.querySelectorAll('[role=option]').forEach(opt => {
        opt.addEventListener('click', () => {
            select.value = opt.dataset.value;

            // Update trigger display: icon badge + label text
            const iconSpan = trigger.querySelector('span > span'); // inner icon container
            const iconEl = iconSpan ? iconSpan.querySelector('.bi') : null;
            if (iconSpan) {
                iconSpan.style.background = opt.dataset.bg;
                if (iconEl) {
                    iconEl.className = 'bi ' + opt.dataset.icon;
                    iconEl.style.color = opt.dataset.color;
                }
            }
            labelEl.textContent = opt.dataset.label;

            // Reset all options, then highlight selected
            listbox.querySelectorAll('[role=option]').forEach(o => {
                o.style.background = 'transparent';
                o.style.fontWeight = '500';
                const ck = o.querySelector('.bi-check2');
                if (ck) ck.remove();
            });
            opt.style.background = '#EEF2FF';
            opt.style.fontWeight = '700';

            close();
            trigger.focus();
        });
    });

    // Close when clicking outside the wrapper
    document.addEventListener('click', e => {
        if (!wrapper.contains(e.target)) close();
    });

});