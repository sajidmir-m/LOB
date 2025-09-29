// Global variables
let issueTypes = [];
let csvKnowledgeBase = {};

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    loadIssueTypes();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    const form = document.getElementById('lobForm');
    form.addEventListener('submit', handleFormSubmit);
    
    const issueTypeSelect = document.getElementById('issueType');
    issueTypeSelect.addEventListener('change', handleIssueTypeChange);
    
    const vocTextarea = document.getElementById('voc');
    vocTextarea.addEventListener('input', handleVocInput);
}

// Load issue types from the API
async function loadIssueTypes() {
    try {
        const response = await fetch('/api/issue-types');
        const data = await response.json();
        
        issueTypes = data.issue_types;
        csvKnowledgeBase = data.knowledge_base;
        
        populateIssueTypeSelect();
        displayCsvInfo();
        displayIssueTypes();
        
    } catch (error) {
        console.error('Error loading issue types:', error);
        showError('Failed to load issue types from CSV knowledge base');
    }
}

// Populate the issue type select dropdown
function populateIssueTypeSelect() {
    const select = document.getElementById('issueType');
    select.innerHTML = '<option value="">Select an issue type...</option>';
    
    issueTypes.forEach(issueType => {
        const option = document.createElement('option');
        option.value = issueType;
        option.textContent = issueType;
        select.appendChild(option);
    });
}

// Display CSV information
function displayCsvInfo() {
    const csvInfo = document.getElementById('csvInfo');
    const csvInfoText = document.getElementById('csvInfoText');
    
    const totalIssues = Object.keys(csvKnowledgeBase).length;
    csvInfoText.textContent = `Loaded ${totalIssues} issue types from CSV knowledge base with SOP rules and resolutions.`;
    csvInfo.style.display = 'block';
}

// Display available issue types
function displayIssueTypes() {
    const issueTypesDiv = document.getElementById('issueTypes');
    const issueTypesList = document.getElementById('issueTypesList');
    
    issueTypesList.innerHTML = '';
    issueTypes.forEach(issueType => {
        const li = document.createElement('li');
        li.textContent = issueType;
        issueTypesList.appendChild(li);
    });
    
    issueTypesDiv.style.display = 'block';
}

// Handle issue type selection change
function handleIssueTypeChange(event) {
    const selectedIssueType = event.target.value;
    const vocTextarea = document.getElementById('voc');
    
    if (selectedIssueType && csvKnowledgeBase[selectedIssueType]) {
        const vocExamples = csvKnowledgeBase[selectedIssueType].voc_examples;
        if (vocExamples && vocExamples.length > 0) {
            // Show VOC examples as placeholder or suggestions
            const exampleText = vocExamples.slice(0, 2).join('\n\n');
            vocTextarea.placeholder = `Examples:\n${exampleText}`;
        }
    } else {
        vocTextarea.placeholder = 'Enter customer\'s statement or voice of customer...';
    }
}

// Handle VOC input for auto-suggestion
function handleVocInput(event) {
    const vocText = event.target.value.toLowerCase();
    
    // Auto-suggest issue type based on VOC content
    if (vocText.length > 10) {
        const suggestedIssueType = findBestIssueTypeMatch(vocText);
        if (suggestedIssueType) {
            const issueTypeSelect = document.getElementById('issueType');
            if (issueTypeSelect.value !== suggestedIssueType) {
                // Highlight the suggested option
                highlightSuggestedOption(suggestedIssueType);
            }
        }
    }
}

// Find best issue type match based on VOC
function findBestIssueTypeMatch(vocText) {
    let bestMatch = null;
    let bestScore = 0;
    
    for (const [issueType, data] of Object.entries(csvKnowledgeBase)) {
        for (const vocExample of data.voc_examples || []) {
            const commonWords = vocText.split(' ').filter(word => 
                vocExample.toLowerCase().includes(word) && word.length > 3
            );
            if (commonWords.length > bestScore) {
                bestScore = commonWords.length;
                bestMatch = issueType;
            }
        }
    }
    
    return bestMatch;
}

// Highlight suggested option
function highlightSuggestedOption(issueType) {
    const select = document.getElementById('issueType');
    const options = select.options;
    
    for (let i = 0; i < options.length; i++) {
        if (options[i].value === issueType) {
            options[i].style.backgroundColor = '#fff3cd';
            options[i].style.fontWeight = 'bold';
            break;
        }
    }
}

// Handle form submission
async function handleFormSubmit(event) {
    event.preventDefault();
    
    const generateBtn = document.getElementById('generateBtn');
    const originalText = generateBtn.textContent;
    
    try {
        // Show loading state
        generateBtn.disabled = true;
        generateBtn.textContent = 'Generating...';
        
        // Get form data
        const formData = new FormData(event.target);
        const data = {
            issue_type: formData.get('issueType'),
            voc: formData.get('voc'),
            stock_available: formData.get('stockAvailable'),
            follow_up_date: formData.get('followUpDate') || null,
            dp_sm_call: formData.get('dpSmCall') || null
        };
        
        // Generate LOB summary
        const response = await fetch('/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        // Display results
        displayResults(result);
        
    } catch (error) {
        console.error('Error generating LOB summary:', error);
        showError('Failed to generate LOB summary. Please try again.');
    } finally {
        // Reset button state
        generateBtn.disabled = false;
        generateBtn.textContent = originalText;
    }
}

// Display results
function displayResults(result) {
    // Display LOB summary
    const lobSummary = document.getElementById('lobSummary');
    lobSummary.textContent = result.summary;
    
    // Display CSV validation if available
    if (result.csv_validation) {
        displayCsvValidation(result.csv_validation);
    }
    
    // Scroll to results
    document.getElementById('results').scrollIntoView({ behavior: 'smooth' });
}

// Display CSV validation results
function displayCsvValidation(validation) {
    const csvValidation = document.getElementById('csvValidation');
    const csvValidationContent = document.getElementById('csvValidationContent');
    
    let validationText = '';
    
    if (validation.matched_issue_type) {
        validationText += `Matched Issue Type: ${validation.matched_issue_type}\n\n`;
    }
    
    if (validation.suggested_resolution) {
        validationText += `Suggested Resolution: ${validation.suggested_resolution}\n\n`;
    }
    
    if (validation.sop_details) {
        validationText += `SOP Details:\n${validation.sop_details}\n\n`;
    }
    
    if (validation.voc_examples && validation.voc_examples.length > 0) {
        validationText += `Related VOC Examples:\n`;
        validation.voc_examples.forEach(example => {
            validationText += `• ${example}\n`;
        });
    }
    
    csvValidationContent.textContent = validationText;
    csvValidation.style.display = 'block';
}

// Show error message
function showError(message) {
    const results = document.getElementById('results');
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error';
    errorDiv.textContent = message;
    
    // Remove existing error messages
    const existingErrors = results.querySelectorAll('.error');
    existingErrors.forEach(error => error.remove());
    
    // Add new error message
    results.insertBefore(errorDiv, results.firstChild);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        errorDiv.remove();
    }, 5000);
}

// Utility function to format date
function formatDate(dateString) {
    if (!dateString) return null;
    
    const date = new Date(dateString);
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    
    return `${day}-${month}-${year}`;
}

// Auto-fill form with example data (for testing)
function fillExampleData() {
    document.getElementById('issueType').value = 'Ordered by Mistake';
    document.getElementById('voc').value = 'I accidentally ordered the wrong product, did not open the package.';
    document.getElementById('stockAvailable').value = 'No';
    document.getElementById('followUpDate').value = '2025-06-25';
}

// Add example button for testing (can be removed in production)
document.addEventListener('DOMContentLoaded', function() {
    const formSection = document.querySelector('.form-section');
    const exampleBtn = document.createElement('button');
    exampleBtn.type = 'button';
    exampleBtn.className = 'btn';
    exampleBtn.style.marginTop = '10px';
    exampleBtn.style.background = 'linear-gradient(135deg, #28a745 0%, #20c997 100%)';
    exampleBtn.textContent = 'Fill Example Data';
    exampleBtn.onclick = fillExampleData;
    
    formSection.appendChild(exampleBtn);
});
