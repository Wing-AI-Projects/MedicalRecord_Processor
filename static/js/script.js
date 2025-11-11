/* ============================================================================
   MEDICAL RECORD PROCESSOR - JAVASCRIPT
   ============================================================================ */

// DOM Elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.querySelector('.file-name');
const clearBtn = document.getElementById('clearBtn');
const uploadBtn = document.getElementById('uploadBtn');
const errorMsg = document.getElementById('errorMsg');
const loadingSpinner = document.getElementById('loadingSpinner');
const resultsSection = document.getElementById('resultsSection');
const emptyState = document.getElementById('emptyState');
const newUploadBtn = document.getElementById('newUploadBtn');
const downloadBtn = document.getElementById('downloadBtn');

// State
let selectedFile = null;
let medicalData = null;

// ============================================================================
// FILE UPLOAD HANDLING
// ============================================================================

// Browse button click
uploadArea.addEventListener('click', () => {
    fileInput.click();
});

// File input change
fileInput.addEventListener('change', (e) => {
    handleFileSelection(e.target.files[0]);
});

// Drag and drop
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    handleFileSelection(e.dataTransfer.files[0]);
});

function handleFileSelection(file) {
    clearError();

    if (!file) {
        clearFileSelection();
        return;
    }

    // Validate file type
    if (file.type !== 'application/pdf') {
        showError('Please select a valid PDF file');
        clearFileSelection();
        return;
    }

    // Validate file size (50MB)
    if (file.size > 50 * 1024 * 1024) {
        showError('File is too large (max 50MB)');
        clearFileSelection();
        return;
    }

    selectedFile = file;
    fileName.textContent = `📄 ${file.name}`;
    fileInfo.classList.remove('hidden');
    uploadBtn.classList.remove('hidden');
}

clearBtn.addEventListener('click', () => {
    clearFileSelection();
});

function clearFileSelection() {
    selectedFile = null;
    fileInput.value = '';
    fileInfo.classList.add('hidden');
    uploadBtn.classList.add('hidden');
}

// ============================================================================
// FILE UPLOAD & PROCESSING
// ============================================================================

uploadBtn.addEventListener('click', uploadFile);

async function uploadFile() {
    if (!selectedFile) {
        showError('Please select a file');
        return;
    }

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
        showLoading();
        clearError();

        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || 'Upload failed');
        }

        if (data.status === 'success') {
            medicalData = data.data;
            displayResults();
            clearFileSelection();
        } else {
            throw new Error(data.message || 'Processing failed');
        }

    } catch (error) {
        showError(error.message || 'An error occurred during upload');
    } finally {
        hideLoading();
    }
}

// ============================================================================
// DISPLAY RESULTS
// ============================================================================

function displayResults() {
    if (!medicalData) return;

    // Show results section, hide empty state
    resultsSection.classList.remove('hidden');
    emptyState.classList.remove('visible');

    // Display overview tab
    displayPatientInfo();
    displayStats();

    // Display diagnoses
    displayDiagnoses();

    // Display medications
    displayMedications();

    // Display lab results
    displayLabResults();

    // Display vital signs
    displayVitals();

    // Display allergies
    displayAllergies();

    // Display clinical notes
    displayNotes();

    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

function displayPatientInfo() {
    const patient = medicalData.patient_info || {};

    document.getElementById('patientSex').textContent = patient.sex || '-';
    document.getElementById('patientAge').textContent = patient.age || '-';
    document.getElementById('patientRace').textContent = patient.race || '-';
    document.getElementById('patientHeight').textContent = patient.height || '-';
    document.getElementById('patientWeight').textContent = patient.weight || '-';
}

function displayStats() {
    const diagnoses = medicalData.diagnoses || [];
    const medications = medicalData.medications || [];
    const labs = medicalData.lab_results || [];
    const allergies = medicalData.allergies || [];

    document.getElementById('diagnosisCount').textContent = diagnoses.length;
    document.getElementById('medicationCount').textContent = medications.length;
    document.getElementById('labCount').textContent = labs.length;
    document.getElementById('allergyCount').textContent = allergies.length;
}

function displayDiagnoses() {
    const container = document.getElementById('diagnosesList');
    const diagnoses = medicalData.diagnoses || [];

    if (diagnoses.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: var(--gray-500);">No diagnoses found</p>';
        return;
    }

    container.innerHTML = diagnoses.map(diagnosis => `
        <div class="list-item diagnosis">
            <div class="item-header">
                <h4 class="item-title">${escapeHtml(diagnosis.description)}</h4>
                ${diagnosis.date ? `<span class="item-date">${formatDate(diagnosis.date)}</span>` : ''}
            </div>
            <div class="item-details">
                ${diagnosis.code ? `
                    <div class="detail-row">
                        <span class="detail-label">ICD Code:</span>
                        <span class="detail-value">${escapeHtml(diagnosis.code)}</span>
                    </div>
                ` : ''}
            </div>
        </div>
    `).join('');
}

function displayMedications() {
    const container = document.getElementById('medicationsList');
    const medications = medicalData.medications || [];

    if (medications.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: var(--gray-500);">No medications found</p>';
        return;
    }

    container.innerHTML = medications.map(med => `
        <div class="list-item medication">
            <div class="item-header">
                <h4 class="item-title">${escapeHtml(med.name)}</h4>
            </div>
            <div class="item-details">
                ${med.dosage ? `
                    <div class="detail-row">
                        <span class="detail-label">Dosage:</span>
                        <span class="detail-value">${escapeHtml(med.dosage)}</span>
                    </div>
                ` : ''}
                ${med.frequency ? `
                    <div class="detail-row">
                        <span class="detail-label">Frequency:</span>
                        <span class="detail-value">${escapeHtml(med.frequency)}</span>
                    </div>
                ` : ''}
                ${med.indication ? `
                    <div class="detail-row">
                        <span class="detail-label">Indication:</span>
                        <span class="detail-value">${escapeHtml(med.indication)}</span>
                    </div>
                ` : ''}
            </div>
        </div>
    `).join('');
}

function displayLabResults() {
    const container = document.getElementById('labsList');
    const labs = medicalData.lab_results || [];

    if (labs.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: var(--gray-500);">No lab results found</p>';
        return;
    }

    container.innerHTML = labs.map(lab => {
        let statusClass = 'status-normal';
        if (lab.status === 'High') statusClass = 'status-high';
        else if (lab.status === 'Low') statusClass = 'status-low';
        else if (lab.status === 'Critical') statusClass = 'status-critical';

        return `
            <div class="list-item lab">
                <div class="item-header">
                    <h4 class="item-title">${escapeHtml(lab.test_name)}</h4>
                    ${lab.date ? `<span class="item-date">${formatDate(lab.date)}</span>` : ''}
                </div>
                <div class="item-details">
                    <div class="detail-row">
                        <span class="detail-label">Result:</span>
                        <span class="detail-value">
                            ${escapeHtml(lab.value)} ${lab.unit ? escapeHtml(lab.unit) : ''}
                        </span>
                    </div>
                    ${lab.reference_range ? `
                        <div class="detail-row">
                            <span class="detail-label">Reference Range:</span>
                            <span class="detail-value">${escapeHtml(lab.reference_range)}</span>
                        </div>
                    ` : ''}
                    ${lab.status ? `
                        <div class="detail-row">
                            <span class="detail-label">Status:</span>
                            <span class="status-badge ${statusClass}">${escapeHtml(lab.status)}</span>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }).join('');
}

function displayVitals() {
    const container = document.getElementById('vitalsList');
    const vitals = medicalData.vital_signs || [];

    if (vitals.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: var(--gray-500);">No vital signs found</p>';
        return;
    }

    container.innerHTML = vitals.map(vital => `
        <div class="list-item vital">
            <div class="item-header">
                <h4 class="item-title">${escapeHtml(vital.parameter)}</h4>
                ${vital.date ? `<span class="item-date">${formatDate(vital.date)}</span>` : ''}
            </div>
            <div class="item-details">
                <div class="detail-row">
                    <span class="detail-label">Value:</span>
                    <span class="detail-value">
                        ${escapeHtml(vital.value)} ${vital.unit ? escapeHtml(vital.unit) : ''}
                    </span>
                </div>
            </div>
        </div>
    `).join('');
}

function displayAllergies() {
    const container = document.getElementById('allergiesList');
    const allergies = medicalData.allergies || [];

    if (allergies.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: var(--gray-500);">No allergies recorded</p>';
        return;
    }

    container.innerHTML = allergies.map(allergy => `
        <div class="list-item allergy">
            <div class="item-header">
                <h4 class="item-title">⚠️ ${escapeHtml(allergy.allergen)}</h4>
            </div>
            <div class="item-details">
                ${allergy.reaction ? `
                    <div class="detail-row">
                        <span class="detail-label">Reaction:</span>
                        <span class="detail-value">${escapeHtml(allergy.reaction)}</span>
                    </div>
                ` : ''}
            </div>
        </div>
    `).join('');
}

function displayNotes() {
    const container = document.getElementById('clinicalNotes');
    const notes = medicalData.clinical_notes || 'No clinical notes available';

    container.textContent = escapeHtml(notes);
}

// ============================================================================
// TAB SWITCHING
// ============================================================================

const tabButtons = document.querySelectorAll('.tab-btn');
const tabPanes = document.querySelectorAll('.tab-pane');

tabButtons.forEach(button => {
    button.addEventListener('click', () => {
        const tabName = button.getAttribute('data-tab');

        // Remove active class from all buttons and panes
        tabButtons.forEach(btn => btn.classList.remove('active'));
        tabPanes.forEach(pane => pane.classList.remove('active'));

        // Add active class to clicked button and corresponding pane
        button.classList.add('active');
        document.getElementById(tabName).classList.add('active');
    });
});

// ============================================================================
// NEW UPLOAD
// ============================================================================

newUploadBtn.addEventListener('click', () => {
    resultsSection.classList.add('hidden');
    emptyState.classList.add('visible');
    medicalData = null;
    clearFileSelection();
    window.scrollTo({ top: 0, behavior: 'smooth' });
});

// ============================================================================
// DOWNLOAD REPORT
// ============================================================================

downloadBtn.addEventListener('click', downloadReport);

function downloadReport() {
    if (!medicalData) return;

    const report = generateReport();
    const blob = new Blob([report], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `medical_report_${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
}

function generateReport() {
    const patient = medicalData.patient_info || {};
    const diagnoses = medicalData.diagnoses || [];
    const medications = medicalData.medications || [];
    const labs = medicalData.lab_results || [];
    const vitals = medicalData.vital_signs || [];
    const allergies = medicalData.allergies || [];
    const notes = medicalData.clinical_notes || '';

    let report = `MEDICAL RECORD REPORT
Generated: ${new Date().toLocaleString()}
================================

PATIENT DEMOGRAPHICS
--------------------
Sex: ${patient.sex || 'N/A'}
Age: ${patient.age || 'N/A'}
Race: ${patient.race || 'N/A'}
Height: ${patient.height || 'N/A'}
Weight: ${patient.weight || 'N/A'}

DIAGNOSES
---------
${diagnoses.map(d => `• ${d.description} (${d.code}) - ${d.date || 'N/A'}`).join('\n') || 'None'}

MEDICATIONS
-----------
${medications.map(m => `• ${m.name}
  Dosage: ${m.dosage || 'N/A'}
  Frequency: ${m.frequency || 'N/A'}
  Indication: ${m.indication || 'N/A'}`).join('\n\n') || 'None'}

LAB RESULTS
-----------
${labs.map(l => `• ${l.test_name}: ${l.value} ${l.unit || ''} (${l.status || 'N/A'})
  Reference Range: ${l.reference_range || 'N/A'}
  Date: ${l.date || 'N/A'}`).join('\n\n') || 'None'}

VITAL SIGNS
-----------
${vitals.map(v => `• ${v.parameter}: ${v.value} ${v.unit || ''} (${v.date || 'N/A'})`).join('\n') || 'None'}

ALLERGIES
---------
${allergies.map(a => `• ${a.allergen}: ${a.reaction || 'N/A'}`).join('\n') || 'None'}

CLINICAL NOTES
---------------
${notes}

================================
End of Report
`;

    return report;
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function showLoading() {
    loadingSpinner.classList.remove('hidden');
    uploadBtn.disabled = true;
}

function hideLoading() {
    loadingSpinner.classList.add('hidden');
    uploadBtn.disabled = false;
}

function showError(message) {
    errorMsg.textContent = message;
    errorMsg.classList.remove('hidden');
}

function clearError() {
    errorMsg.classList.add('hidden');
}

function formatDate(dateString) {
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    } catch {
        return dateString;
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

// ============================================================================
// INITIALIZATION
// ============================================================================

// Show empty state on page load
document.addEventListener('DOMContentLoaded', () => {
    emptyState.classList.add('visible');
});
