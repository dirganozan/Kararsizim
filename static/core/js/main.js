/**
 * KRARSIZIM - CLIENT-SIDE JAVASCRIPT
 * Handles Modal, Dynamic Poll Options (2-5 constraint), AJAX Voting, and Toast Alerts.
 */

// Helper to get CSRF token
function getCsrfToken() {
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    if (metaTag && metaTag.content) {
        return metaTag.content;
    }
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
    return cookieValue || '';
}

// Helper to escape HTML characters
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Global Toast Notification Helper
function showToast(message, type = 'info') {
    let container = document.querySelector('.messages-wrapper');
    if (!container) {
        container = document.createElement('div');
        container.className = 'messages-wrapper';
        const mainContent = document.querySelector('.main-content .container');
        if (mainContent) {
            mainContent.insertBefore(container, mainContent.firstChild);
        } else {
            document.body.appendChild(container);
        }
    }

    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    const icon = type === 'success' ? '✨' : (type === 'error' ? '⚠️' : 'ℹ️');
    alert.innerHTML = `<span>${icon}</span><div>${message}</div>`;
    container.appendChild(alert);

    setTimeout(() => {
        alert.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-6px)';
        setTimeout(() => alert.remove(), 400);
    }, 4500);
}

// Global options manager initializer (for Poll Creation)
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

        if (count >= MAX_OPTIONS) {
            addBtn.disabled = true;
            addBtn.style.opacity = '0.5';
            addBtn.style.cursor = 'not-allowed';
        } else {
            addBtn.disabled = false;
            addBtn.style.opacity = '1';
            addBtn.style.cursor = 'pointer';
        }

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
        const newInput = newRow.querySelector('.option-input');
        if (newInput) newInput.focus();

        updateOptionsState();
    });

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

    updateOptionsState();
}

// Global Interactive Voting Handler (FAZ 3)
async function handleVoteClick(btn) {
    const pollId = btn.dataset.pollId;
    const optionId = btn.dataset.optionId;
    if (!pollId || !optionId) return;

    const card = document.getElementById(`poll-card-${pollId}`);
    const optionsWrapper = document.getElementById(`poll-options-${pollId}`);
    if (!optionsWrapper) return;

    // Temporarily disable buttons inside this poll
    const buttons = optionsWrapper.querySelectorAll('.poll-option-btn');
    buttons.forEach(b => {
        b.disabled = true;
        b.style.pointerEvents = 'none';
    });

    btn.style.borderColor = 'var(--primary)';
    btn.style.background = 'var(--primary-light)';
    const indicator = btn.querySelector('.vote-indicator');
    if (indicator) indicator.textContent = '⏳';

    try {
        const response = await fetch(`/api/poll/${pollId}/vote/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ option_id: optionId })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            if (card) {
                card.classList.add('just-voted');
                setTimeout(() => card.classList.remove('just-voted'), 500);
            }

            // Morph options into animated progress bar results
            const colorClasses = ['color-opt-0', 'color-opt-1', 'color-opt-2', 'color-opt-3', 'color-opt-4'];
            let resultsHtml = '';

            data.options.forEach((opt, idx) => {
                const isSelected = (opt.id == data.user_voted_option_id);
                const colorClass = colorClasses[idx % colorClasses.length];
                resultsHtml += `
                    <div class="poll-result-row ${isSelected ? 'selected-by-user' : ''}">
                        <div class="poll-progress-fill ${colorClass}" style="width: 0%;" data-target-width="${opt.percentage}%"></div>
                        <div class="poll-progress-content">
                            <span class="poll-option-label">
                                ${escapeHtml(opt.text)}
                                ${isSelected ? '<span class="voted-badge">✓ Senin Oyun</span>' : ''}
                            </span>
                            <span class="poll-percentage">
                                %${opt.percentage}
                                <span class="poll-vote-count">(${opt.vote_count} oy)</span>
                            </span>
                        </div>
                    </div>
                `;
            });

            optionsWrapper.innerHTML = resultsHtml;

            // Trigger animation
            requestAnimationFrame(() => {
                optionsWrapper.querySelectorAll('.poll-progress-fill').forEach(fill => {
                    fill.style.width = fill.dataset.targetWidth;
                });
            });

            // Update total votes in footer
            const totalVotesEl = document.getElementById(`poll-total-votes-${pollId}`);
            if (totalVotesEl) {
                totalVotesEl.innerHTML = `🗳️ Toplam <strong class="total-votes-number">${data.total_votes}</strong> oy`;
            }

            // Update status badge
            const statusBadge = document.getElementById(`poll-status-${pollId}`);
            if (statusBadge) {
                statusBadge.textContent = '✅ Oy kullandın';
                statusBadge.style.color = 'var(--accent-green)';
            }

            showToast(data.message || 'Oyunuz başarıyla kaydedildi!', 'success');
        } else {
            showToast(data.error || 'Oy kullanılırken bir hata oluştu.', 'error');
            buttons.forEach(b => {
                b.disabled = false;
                b.style.pointerEvents = '';
            });
            if (indicator) indicator.textContent = '✓';
        }
    } catch (err) {
        console.error('Oylama hatası:', err);
        showToast('Bağlantı hatası oluştu, lütfen tekrar deneyin.', 'error');
        buttons.forEach(b => {
            b.disabled = false;
            b.style.pointerEvents = '';
        });
        if (indicator) indicator.textContent = '✓';
    }
}

// DOM Ready
document.addEventListener('DOMContentLoaded', () => {
    // 1. Auto-dismiss existing alerts
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-6px)';
            setTimeout(() => alert.remove(), 400);
        }, 5000);
    });

    // 1.1 Clear legacy client-side localStorage vote locks so they never interfere with user accounts
    try {
        const keysToRemove = [];
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && key.startsWith('krarsizim_voted_')) {
                keysToRemove.push(key);
            }
        }
        keysToRemove.forEach(k => localStorage.removeItem(k));
    } catch (e) {
        // Ignore if storage is inaccessible
    }

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

    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeModal();
        });
    }

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

            const lowerSet = new Set(cleanOptions.map(o => o.toLowerCase()));
            if (lowerSet.size !== cleanOptions.length) {
                showModalError('Seçenekler birbirinden farklı olmalıdır.');
                return;
            }

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
                    window.location.href = data.redirect_url || '/';
                } else {
                    const errorMsg = data.errors ? data.errors.join('<br>') : 'Bir hata oluştu.';
                    showModalError(errorMsg);
                }
            } catch (err) {
                console.error('Anket oluşturma hatası:', err);
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

// ==========================================================================
// AUTHOR ACTIONS: TOGGLE STATUS & DELETE POLL
// ==========================================================================

async function handleTogglePollStatus(pollId) {
    if (!pollId) return;

    const btn = document.getElementById(`toggle-btn-${pollId}`);
    if (btn) {
        btn.disabled = true;
        btn.textContent = 'İşleniyor...';
    }

    try {
        const response = await fetch(`/polls/${pollId}/toggle-status/`, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCsrfToken()
            }
        });

        const data = await response.json();

        if (response.ok && data.success) {
            showToast(data.message, 'success');
            setTimeout(() => {
                window.location.reload();
            }, 400);
        } else {
            showToast(data.error || 'İşlem gerçekleştirilemedi.', 'error');
            if (btn) btn.disabled = false;
        }
    } catch (err) {
        console.error('Anket durumu değiştirme hatası:', err);
        showToast('Bağlantı hatası oluştu.', 'error');
        if (btn) btn.disabled = false;
    }
}

async function handleDeletePoll(pollId) {
    if (!pollId) return;

    const confirmed = confirm('Bu anketi ve kullanılan tüm oyları kalıcı olarak silmek istediğinize emin misiniz?');
    if (!confirmed) return;

    const card = document.getElementById(`poll-card-${pollId}`);

    try {
        const response = await fetch(`/polls/${pollId}/delete/`, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCsrfToken()
            }
        });

        const data = await response.json();

        if (response.ok && data.success) {
            showToast(data.message, 'info');
            if (card) {
                card.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                card.style.opacity = '0';
                card.style.transform = 'scale(0.95)';
                setTimeout(() => card.remove(), 300);
            } else {
                window.location.reload();
            }
        } else {
            showToast(data.error || 'Silme işlemi gerçekleştirilemedi.', 'error');
        }
    } catch (err) {
        console.error('Anket silme hatası:', err);
        showToast('Bağlantı hatası oluştu.', 'error');
    }
}

// Global Double-Submit Prevention for Standard Forms (e.g. Register, Login)
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('form[method="post"]:not([data-ajax="true"])').forEach(form => {
        form.addEventListener('submit', (e) => {
            if (form.dataset.submitting === 'true') {
                e.preventDefault();
                return false;
            }
            form.dataset.submitting = 'true';
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                // Disable button slightly after submit event to allow form dispatch
                setTimeout(() => {
                    submitBtn.disabled = true;
                    submitBtn.style.opacity = '0.75';
                    submitBtn.style.cursor = 'wait';
                    submitBtn.innerHTML = '<span>⏳ Lütfen bekleyin...</span>';
                }, 10);
            }
        });
    });
});
