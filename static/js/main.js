import { deletePatient, extractPatient, fetchPatients } from './api.js';
import { elements } from './dom.js';
import { hideError, showError, showToast } from './feedback.js';
import { closeAbout, closePatientModal, openAbout, openPatientModal, resetDeleteButton } from './modal.js';
import { renderFilterCounts, renderPatientList, renderResults } from './render.js';

let currentFilter = 'all';
let allPatients = [];
let currentModalPatientId = null;
let deleteConfirm = false;

function updateClock() {
    const now = new Date();
    const hours = now.getHours().toString().padStart(2, '0');
    const minutes = now.getMinutes().toString().padStart(2, '0');
    elements.clockTime.textContent = `${hours}:${minutes}`;
}

function renderQueue() {
    renderFilterCounts(allPatients);
    renderPatientList(allPatients, currentFilter);
}

async function loadPatients() {
    try {
        allPatients = await fetchPatients();
        renderQueue();
    } catch (error) {
        console.error('Failed to load patients:', error);
        elements.patientList.innerHTML = `
            <div class="empty-state">
                <p>Failed to load patient queue</p>
            </div>
        `;
    }
}

async function handleFile(file) {
    if (!file.type.startsWith('image/')) {
        showToast('Please upload an image file', 'error');
        return;
    }

    hideError();
    elements.resultsSection.classList.add('hidden');
    elements.loading.classList.add('active');
    elements.loadingText.textContent = 'Uploading and analyzing form...';

    const reader = new FileReader();
    reader.onload = (event) => {
        elements.previewImage.src = event.target.result;
        elements.previewWrapper.classList.remove('hidden');
    };
    reader.readAsDataURL(file);

    try {
        const data = await extractPatient(file);
        elements.loading.classList.remove('active');
        renderResults(data);
        await loadPatients();
        showToast('Patient analyzed and added to queue');
    } catch (error) {
        elements.loading.classList.remove('active');
        showError('Analysis Failed', error.message);
        console.error('Upload error:', error);
    }
}

function closeModal() {
    closePatientModal();
    currentModalPatientId = null;
    deleteConfirm = false;
}

async function handleDelete() {
    if (!currentModalPatientId) return;

    if (!deleteConfirm) {
        deleteConfirm = true;
        elements.modalDelete.classList.add('confirm');
        elements.deleteLabel.textContent = 'Confirm Delete';
        return;
    }

    try {
        await deletePatient(currentModalPatientId);
        closeModal();
        await loadPatients();
        showToast('Patient deleted');
    } catch (error) {
        showToast(`Delete failed: ${error.message}`, 'error');
    }
}

function openModalForPatient(patient) {
    currentModalPatientId = patient.id;
    deleteConfirm = false;
    resetDeleteButton();
    openPatientModal(patient);
}

function setupEventListeners() {
    elements.captureBtn.addEventListener('click', (event) => {
        if (event.target !== elements.captureInput) elements.captureInput.click();
    });

    elements.captureBtn.addEventListener('dragover', (event) => {
        event.preventDefault();
        elements.captureBtn.classList.add('dragover');
    });

    elements.captureBtn.addEventListener('dragleave', () => {
        elements.captureBtn.classList.remove('dragover');
    });

    elements.captureBtn.addEventListener('drop', (event) => {
        event.preventDefault();
        elements.captureBtn.classList.remove('dragover');
        const files = event.dataTransfer.files;
        if (files.length > 0) handleFile(files[0]);
    });

    elements.captureInput.addEventListener('change', (event) => {
        if (event.target.files.length > 0) handleFile(event.target.files[0]);
    });

    elements.filterTabs.addEventListener('click', (event) => {
        const tab = event.target.closest('.filter-tab');
        if (!tab) return;

        currentFilter = tab.dataset.filter;
        document.querySelectorAll('.filter-tab').forEach((filterTab) => filterTab.classList.remove('active'));
        tab.classList.add('active');
        renderPatientList(allPatients, currentFilter);
    });

    elements.modalClose.addEventListener('click', closeModal);
    elements.modalDelete.addEventListener('click', handleDelete);
    elements.modalOverlay.addEventListener('click', (event) => {
        if (event.target === elements.modalOverlay) closeModal();
    });

    elements.aboutBtn.addEventListener('click', openAbout);
    elements.aboutClose.addEventListener('click', closeAbout);
    elements.aboutOverlay.addEventListener('click', (event) => {
        if (event.target === elements.aboutOverlay) closeAbout();
    });

    elements.printBtn.addEventListener('click', () => window.print());

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            closeModal();
            closeAbout();
        }
    });

    elements.patientList.addEventListener('click', (event) => {
        const item = event.target.closest('.patient-item');
        if (!item) return;

        const id = parseInt(item.dataset.id, 10);
        const patient = allPatients.find((candidate) => candidate.id === id);
        if (patient) openModalForPatient(patient);
    });
}

function init() {
    updateClock();
    setInterval(updateClock, 1000);
    setupEventListeners();
    loadPatients();
}

init();
