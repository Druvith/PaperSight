import { elements } from './dom.js';
import { escapeHtml, formatTime, isMissingValue } from './format.js';

const PATIENT_FIELDS = [
    { key: 'patient_name', label: 'Patient Name' },
    { key: 'age', label: 'Age' },
    { key: 'gender', label: 'Gender' },
    { key: 'chief_complaint', label: 'Chief Complaint' },
    { key: 'duration', label: 'Duration' },
    { key: 'allergies', label: 'Allergies' },
    { key: 'medications', label: 'Medications' },
    { key: 'referred_by', label: 'Referred By' },
];

function patientNameHtml(patient) {
    if (!patient.patient_name || patient.patient_name === 'unreadable') {
        return '<span class="patient-name unknown">Unknown Patient</span>';
    }

    return escapeHtml(patient.patient_name);
}

export function renderFieldGrid(data, container) {
    container.innerHTML = PATIENT_FIELDS.map((field) => {
        const value = data[field.key] || '';
        const isMissing = isMissingValue(value);
        const displayValue = isMissing ? '\u2014' : escapeHtml(value);
        const statusClass = isMissing ? 'missing' : 'extracted';
        const dotClass = isMissing ? 'miss' : 'ok';

        return `<div class="data-cell"><div class="data-label"><span class="field-status ${dotClass}"></span>${field.label}</div><div class="data-value ${statusClass}">${displayValue}</div></div>`;
    }).join('');
}

export function renderResults(data) {
    elements.resultsSection.classList.remove('hidden');

    const triage = data.triage;
    const extracted = data.extracted;

    elements.triageBanner.className = `triage-banner ${triage.priority}`;
    elements.triageIndicator.className = `triage-indicator ${triage.priority} stamp-in`;
    elements.triageIndicator.textContent = (triage.priority || '--').toUpperCase();
    setTimeout(() => elements.triageIndicator.classList.remove('stamp-in'), 500);
    elements.triageTitle.textContent = triage.priority_label || '--';
    elements.triageAction.textContent = triage.action || '--';
    elements.triageWait.textContent = triage.wait_time || '--';

    renderFieldGrid(extracted, elements.dataGrid);
    elements.resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

export function renderFilterCounts(patients) {
    const counts = { all: patients.length, red: 0, yellow: 0, green: 0 };
    patients.forEach((patient) => {
        if (counts[patient.priority] !== undefined) counts[patient.priority]++;
    });

    document.getElementById('countAll').textContent = counts.all;
    document.getElementById('countRed').textContent = counts.red;
    document.getElementById('countYellow').textContent = counts.yellow;
    document.getElementById('countGreen').textContent = counts.green;
}

export function renderPatientList(patients, currentFilter) {
    const filtered = currentFilter === 'all'
        ? patients
        : patients.filter((patient) => patient.priority === currentFilter);

    elements.queueCount.textContent = `${filtered.length} patient${filtered.length !== 1 ? 's' : ''}`;

    if (filtered.length === 0) {
        elements.patientList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
                    </svg>
                </div>
                <p>No patients in this category</p>
            </div>
        `;
        return;
    }

    elements.patientList.innerHTML = filtered.map((patient, index) => `
        <div class="patient-item ${escapeHtml(patient.priority)} animate-in" data-id="${patient.id}" style="animation-delay: ${index * 0.05}s">
            <div class="patient-priority ${escapeHtml(patient.priority)}">${(patient.priority || 'G').charAt(0).toUpperCase()}</div>
            <div class="patient-info">
                <div class="patient-name">${patientNameHtml(patient)}</div>
                <div class="patient-details">${escapeHtml(patient.age || '?')}y \u00b7 ${escapeHtml(patient.chief_complaint || '\u2014')}</div>
            </div>
            <div class="patient-time">${escapeHtml(formatTime(patient.created_at))}</div>
        </div>
    `).join('');
}
