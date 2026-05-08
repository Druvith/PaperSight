const API_BASE = '';

async function readJson(response) {
    try {
        return await response.json();
    } catch {
        return {};
    }
}

export async function fetchPatients() {
    const response = await fetch(`${API_BASE}/api/patients`);
    const data = await readJson(response);

    if (!response.ok) {
        throw new Error(data.detail || data.error || `HTTP ${response.status}`);
    }

    return data.patients || [];
}

export async function extractPatient(file) {
    const formData = new FormData();
    formData.append('photo', file);

    const response = await fetch(`${API_BASE}/api/extract`, {
        method: 'POST',
        body: formData,
    });
    const data = await readJson(response);

    if (!response.ok) {
        throw new Error(data.detail || data.error || `HTTP ${response.status}`);
    }

    return data;
}

export async function deletePatient(patientId) {
    const response = await fetch(`${API_BASE}/api/patients/${patientId}`, { method: 'DELETE' });
    const data = await readJson(response);

    if (!response.ok) {
        throw new Error(data.detail || data.error || `HTTP ${response.status}`);
    }

    return data;
}
