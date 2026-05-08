import { elements, setBodyScrollLocked } from './dom.js';
import { escapeHtml } from './format.js';
import { renderFieldGrid } from './render.js';

export function resetDeleteButton() {
    elements.modalDelete.classList.remove('confirm');
    elements.deleteLabel.textContent = 'Delete';
}

export function openPatientModal(patient) {
    resetDeleteButton();

    const modalName = (!patient.patient_name || patient.patient_name === 'unreadable')
        ? 'Unknown Patient'
        : patient.patient_name;
    elements.modalTitle.textContent = modalName;

    const dataGridHtml = document.createElement('div');
    dataGridHtml.classList.add('data-grid');
    renderFieldGrid(patient, dataGridHtml);

    const rules = patient.matched_rules ? patient.matched_rules.split(',') : [];
    const descriptions = patient.matched_descriptions ? patient.matched_descriptions.split('; ') : [];
    const rulesHtml = descriptions.length > 0 && descriptions[0] !== ''
        ? `<div class="rules-list">${descriptions.map((description, index) => {
            const ruleLabel = rules[index] ? `${escapeHtml(rules[index].trim())}: ` : '';
            return `<span class="rule-tag">${ruleLabel}${escapeHtml(description.trim())}</span>`;
        }).join('')}</div>`
        : '<p style="color: var(--text-muted); font-size: 13px;">No specific rules matched</p>';

    const escalationHtml = patient.escalated
        ? `<div class="modal-section">
            <div class="modal-section-title">Escalation</div>
            <div class="escalation-box">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                </svg>
                <span class="escalation-text">${escapeHtml(patient.escalation_reason || 'Escalated due to risk factors')}</span>
            </div>
        </div>`
        : '';

    elements.modalBody.innerHTML = `
        <div class="triage-banner ${escapeHtml(patient.priority)}" style="border-radius: 0;">
            <div class="triage-indicator ${escapeHtml(patient.priority)} stamp-in">${escapeHtml((patient.priority || '--').toUpperCase())}</div>
            <div class="triage-info">
                <h3>${escapeHtml(patient.priority_label || '--')}</h3>
                <p>${escapeHtml(patient.action || '--')}</p>
            </div>
            <div class="triage-meta">
                <div class="triage-wait">${escapeHtml(patient.wait_time || '--')}</div>
                <div class="triage-wait-label">Wait Time</div>
            </div>
        </div>
        <div class="modal-pad">
            <div class="modal-section">
                <div class="modal-section-title">Extracted Data</div>
                ${dataGridHtml.outerHTML}
            </div>
            <div class="modal-section">
                <div class="modal-section-title">Matched Rules</div>
                ${rulesHtml}
            </div>
            ${escalationHtml}
            <div class="modal-section">
                <div class="modal-section-title">Metadata</div>
                <div class="data-grid" style="grid-template-columns: 1fr 1fr;">
                    <div class="data-cell">
                        <div class="data-label">Patient ID</div>
                        <div class="data-value">#${escapeHtml(patient.id)}</div>
                    </div>
                    <div class="data-cell">
                        <div class="data-label">Admitted</div>
                        <div class="data-value">${escapeHtml(patient.created_at || '--')}</div>
                    </div>
                </div>
            </div>
        </div>
    `;

    elements.modalOverlay.classList.add('active');
    setBodyScrollLocked(true);
}

export function closePatientModal() {
    elements.modalOverlay.classList.remove('active');
    setBodyScrollLocked(false);
    resetDeleteButton();
}

export function openAbout() {
    elements.aboutOverlay.classList.add('active');
    setBodyScrollLocked(true);
}

export function closeAbout() {
    elements.aboutOverlay.classList.remove('active');
    setBodyScrollLocked(false);
}
