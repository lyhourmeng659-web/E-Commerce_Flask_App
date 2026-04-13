document.addEventListener('DOMContentLoaded', () => {

    //  Custom category dropdown
    const trigger = document.getElementById('cat-trigger');
    const listbox = document.getElementById('cat-listbox');
    const select = document.getElementById('category_id');
    const label = document.getElementById('cat-label');
    const chevron = document.getElementById('cat-chevron');

    // Only run on pages that include the category dropdown
    if (!trigger || !listbox || !select) return;

    // Wrap in a relative container so the floating listbox positions correctly
    const wrapper = document.createElement('div');
    wrapper.style.position = 'relative';
    trigger.parentNode.insertBefore(wrapper, trigger);
    wrapper.appendChild(trigger);
    wrapper.appendChild(listbox);

    //  Restore pre-selected value (edit mode or after a POST validation fail)
    const preSelected = select.value;
    if (preSelected) {
        const match = listbox.querySelector(`[data-value="${preSelected}"]`);
        if (match) {
            label.textContent = match.dataset.label;
            label.style.color = '#0F172A';
            markSelected(match);
        }
    }

    //  Open / Close helpers
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
        trigger.style.borderColor = select.value ? '#4F46E5' : '#E2E8F0';
        trigger.style.background = '#F8FAFC';
        trigger.style.boxShadow = 'none';
        chevron.style.transform = 'rotate(0deg)';
        trigger.setAttribute('aria-expanded', 'false');
    }

    //  Highlight the active option
    function markSelected(activeEl) {
        // Reset all options
        listbox.querySelectorAll('.cat-check').forEach(c => c.style.display = 'none');
        listbox.querySelectorAll('[role=option]').forEach(o => {
            o.style.fontWeight = '500';
            o.style.color = '#0F172A';
        });
        // Apply active state to chosen option
        if (activeEl && activeEl.dataset.value) {
            const check = activeEl.querySelector('.cat-check');
            if (check) check.style.display = 'block';
            activeEl.style.fontWeight = '700';
            activeEl.style.color = '#4F46E5';
        }
    }

    //  Event listeners

    // Toggle on trigger click
    trigger.addEventListener('click', () => {
        listbox.style.display === 'block' ? close() : open();
    });

    // Keyboard: Enter/Space to open, Escape to close
    trigger.addEventListener('keydown', e => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            open();
        }
        if (e.key === 'Escape') close();
    });

    // Select an option
    listbox.querySelectorAll('[role=option][data-value]').forEach(opt => {
        opt.addEventListener('click', () => {
            select.value = opt.dataset.value;
            label.textContent = opt.dataset.label;
            label.style.color = opt.dataset.value ? '#0F172A' : '#94A3B8';
            markSelected(opt.dataset.value ? opt : null);
            close();
            trigger.focus();
        });
    });

    // Close when clicking outside the wrapper
    document.addEventListener('click', e => {
        if (!wrapper.contains(e.target)) close();
    });

});


// Image upload preview
// Global scope required — called by onchange="previewImage(this)" on <input type="file">
function previewImage(input) {
    const container = document.getElementById('imagePreviewContainer');
    const preview = document.getElementById('imagePreview');
    if (!container || !preview) return;

    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = e => {
            preview.src = e.target.result;
            container.style.display = 'flex';
        };
        reader.readAsDataURL(input.files[0]);
    } else {
        container.style.display = 'none';
    }
}