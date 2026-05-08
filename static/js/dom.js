function byId(id) {
    return document.getElementById(id);
}

export const elements = {
    aboutBtn: byId('aboutBtn'),
    aboutClose: byId('aboutClose'),
    aboutOverlay: byId('aboutOverlay'),
    captureBtn: byId('captureBtn'),
    captureInput: byId('captureInput'),
    clockTime: byId('clockTime'),
    dataGrid: byId('dataGrid'),
    deleteLabel: byId('deleteLabel'),
    errorBanner: byId('errorBanner'),
    errorDetail: byId('errorDetail'),
    errorTitle: byId('errorTitle'),
    filterTabs: byId('filterTabs'),
    loading: byId('loading'),
    loadingText: byId('loadingText'),
    modalBody: byId('modalBody'),
    modalClose: byId('modalClose'),
    modalDelete: byId('modalDelete'),
    modalOverlay: byId('modalOverlay'),
    modalTitle: byId('modalTitle'),
    patientList: byId('patientList'),
    previewImage: byId('previewImage'),
    previewWrapper: byId('previewWrapper'),
    printBtn: byId('printBtn'),
    queueCount: byId('queueCount'),
    resultsSection: byId('resultsSection'),
    toast: byId('toast'),
    triageAction: byId('triageAction'),
    triageBanner: byId('triageBanner'),
    triageIndicator: byId('triageIndicator'),
    triageTitle: byId('triageTitle'),
    triageWait: byId('triageWait'),
};

export function setBodyScrollLocked(isLocked) {
    document.body.style.overflow = isLocked ? 'hidden' : '';
}
