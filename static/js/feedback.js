import { elements } from './dom.js';

export function showToast(message, type = '') {
    elements.toast.textContent = message;
    elements.toast.className = `toast ${type}`;
    requestAnimationFrame(() => elements.toast.classList.add('show'));
    setTimeout(() => elements.toast.classList.remove('show'), 3000);
}

export function showError(title, detail) {
    elements.errorTitle.textContent = title;
    elements.errorDetail.textContent = detail;
    elements.errorBanner.classList.add('active');
}

export function hideError() {
    elements.errorBanner.classList.remove('active');
}
