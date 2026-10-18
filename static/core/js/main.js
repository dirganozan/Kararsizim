/**
 * KRARSIZIM - CLIENT-SIDE JAVASCRIPT
 * Handles Modal, Dynamic Poll Options (2-5 constraint), and AJAX actions.
 */

// Global options manager initializer
function initOptionsManager(config) {
    const container = document.getElementById(config.containerId);
    const addBtn = document.getElementById(config.addBtnId);
    const countBadge = document.getElementById(config.countId);

    if (!container || !addBtn) return;

    const MIN_OPTIONS = 2;
    const MAX_OPTIONS = 5;

    function updateOptionsState() {
        const rows = container.querySelectorAll('.option-row');
        const count = rows.length;

        if (countBadge) {
            countBadge.textContent = `${count} / ${MAX_OPTIONS} Seçenek`;
        }

        // Enable or disable add button
        if (count >= MAX_OPTIONS) {
            addBtn.disabled = true;
            addBtn.style.opacity = '0.5';
            addBtn.style.cursor = 'not-allowed';
        } else {
            addBtn.disabled = false;
            addBtn.style.opacity = '1';
            addBtn.style.cursor = 'pointer';
        }

        // Update labels, numbers and remove buttons
        rows.forEach((row, index) => {
            const num = index + 1;
            const numberSpan = row.querySelector('.option-number');
            const input = row.querySelector('.option-input');
            const removeBtn = row.querySelector('.btn-remove-option');

            if (numberSpan) numberSpan.textContent = num;
            if (input) input.placeholder = `${num}. Seçenek`;

            if (removeBtn) {
                removeBtn.disabled = (count <= MIN_OPTIONS);
            }
        });
    }

    // Add option click handler
    addBtn.addEventListener('click', () => {
        const rows = container.querySelectorAll('.option-row');
        if (rows.length >= MAX_OPTIONS) return;

        const newIndex = rows.length + 1;
        const newRow = document.createElement('div');
        newRow.className = 'option-row';
        newRow.innerHTML = `
            <span class="option-number">${newIndex}</span>
            <input type="text" name="options" class="form-input option-input" placeholder="${newIndex}. Seçenek" maxlength="120" required>
            <button type="button" class="btn-remove-option" title="Seçeneği kaldır" aria-label="Seçeneği kaldır">✕</button>
        `;

        container.appendChild(newRow);
        
        // Focus the newly added input
        const newInput = newRow.querySelector('.option-input');
        if (newInput) newInput.focus();

        updateOptionsState();
    });

    // Delegate remove button click
    container.addEventListener('click', (e) => {
        const removeBtn = e.target.closest('.btn-remove-option');
        if (!removeBtn) return;

        const rows = container.querySelectorAll('.option-row');
        if (rows.length <= MIN_OPTIONS) return;

        const row = removeBtn.closest('.option-row');
        if (row) {
            row.style.transition = 'opacity 0.2s ease, transform 0.2s ease';
            row.style.opacity = '0';
            row.style.transform = 'translateY(-6px)';
            setTimeout(() => {
                row.remove();
                updateOptionsState();
            }, 200);
        }
    });

    // Initial check
    updateOptionsState();
}

document.addEventListener('DOMContentLoaded', () => {
    // 1. Auto-dismiss alerts
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-6px)';
            setTimeout(() => alert.remove(), 400);
        }, 5000);
    });

    // 2. Modal Management
    const modal = document.getElementById('createPollModal');
    const openBtn = document.getElementById('openCreatePollModalBtn');
    const closeBtn = document.getElementById('closeCreatePollModalBtn');
    const cancelBtn = document.getElementById('cancelModalBtn');
    const modalForm = document.getElementById('modalPollForm');
    const modalErrors = document.getElementById('modalFormErrors');

    function openModal() {
        if (!modal) return;
        modal.classList.add('active');
        modal.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';
        const questionInput = document.getElementById('modalQuestionInput');
        if (questionInput) setTimeout(() => questionInput.focus(), 100);
    }

    function closeModal() {
        if (!modal) return;
        modal.classList.remove('active');
        modal.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = '';
        if (modalErrors) modalErrors.style.display = 'none';
    }

    if (openBtn) openBtn.addEventListener('click', openModal);
    if (closeBtn) closeBtn.addEventListener('click', closeModal);
    if (cancelBtn) cancelBtn.addEventListener('click', closeModal);

    // Close when clicking outside dialog
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeModal();
        });
    }

    // Close on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal && modal.classList.contains('active')) {
            closeModal();
        }
    });

    // Initialize Modal Options Manager
    if (document.getElementById('modalOptionsContainer')) {
        initOptionsManager({
            containerId: 'modalOptionsContainer',
            addBtnId: 'modalAddOptionBtn',
            countId: 'modalOptionsCount',
        });
    }

    // Modal Form AJAX Submit
    if (modalForm) {
        modalForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            // Client-side quick validation
            const questionInput = document.getElementById('modalQuestionInput');
            const optionInputs = modalForm.querySelectorAll('.option-input');
            const submitBtn = document.getElementById('submitModalBtn');

            if (!questionInput || questionInput.value.trim().length < 5) {
                showModalError('Lütfen en az 5 karakterlik bir soru yazın.');
                questionInput.focus();
                return;
            }

            const cleanOptions = [];
            optionInputs.forEach(input => {
                const val = input.value.trim();
                if (val) cleanOptions.push(val);
            });

            if (cleanOptions.length < 2) {
                showModalError('En az 2 seçenek doldurmalısınız.');
                return;
            }
            if (cleanOptions.length > 5) {
                showModalError('En fazla 5 seçenek ekleyebilirsiniz.');
                return;
            }

            // Check duplicates
            const lowerSet = new Set(cleanOptions.map(o => o.toLowerCase()));
            if (lowerSet.size !== cleanOptions.length) {
                showModalError('Seçenekler birbirinden farklı olmalıdır.');
                return;
            }

            // Submit via Fetch
            const formData = new FormData(modalForm);
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Yayınlanıyor...';
            }

            try {
                const response = await fetch(modalForm.action, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: formData
                });

                const data = await response.json();

                if (response.ok && data.success) {
                    closeModal();
                    // Redirect to home/index to see newly created poll
                    window.location.href = data.redirect_url || '/';
                } else {
                    const errorMsg = data.errors ? data.errors.join('<br>') : 'Bir hata oluştu.';
                    showModalError(errorMsg);
                }
            } catch (err) {
                console.error('Anket oluşturma hatası:', err);
                // Fallback to regular form submit if fetch fails
                modalForm.submit();
            } finally {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = '🚀 Anketi Yayınla';
                }
            }
        });
    }

    function showModalError(msg) {
        if (!modalErrors) return;
        modalErrors.innerHTML = `⚠️ ${msg}`;
        modalErrors.style.display = 'block';
    }
});
