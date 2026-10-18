/**
 * KRARSIZIM - MAIN CLIENT JAVASCRIPT
 * Prepared for Faz 1, 2, and 3.
 */

document.addEventListener('DOMContentLoaded', () => {
    // Auto-dismiss alert messages after 5 seconds if desired
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-6px)';
            setTimeout(() => alert.remove(), 400);
        }, 5000);
    });
});
