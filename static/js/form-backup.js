
document.addEventListener('DOMContentLoaded', () => {
    const forms = document.querySelectorAll('form');
    
    forms.forEach((form, index) => {


        const formIdentifier = form.id || form.name || `form_${index}`;
        const storageKey = `form_backup_${window.location.pathname}_${formIdentifier}`;
        

        const savedString = localStorage.getItem(storageKey);
        if (savedString) {
            const savedData = JSON.parse(savedString);
            
            Object.keys(savedData).forEach(name => {
        
                const inputs = form.querySelectorAll(`[name="${name}"]`);
                
                inputs.forEach(input => {
                    if (input.type === 'radio' || input.type === 'checkbox') {
                        if (savedData[name] === input.value) {
                            input.checked = true;
                        }
                    } else {
                
                        if (!input.value) {
                            input.value = savedData[name];
                        }
                    }
                });
            });
        }
        


        const saveFormData = () => {
            const formData = new FormData(form);
            const dataObj = Object.fromEntries(formData.entries());
            localStorage.setItem(storageKey, JSON.stringify(dataObj));
        };
        

        form.addEventListener('input', saveFormData);
        form.addEventListener('change', saveFormData);
    });
});

/**
 * Clear form backup from localStorage
 * Call this function on success pages to remove saved form data
 * @param {string} formUrlPath - The path of the form page (e.g., '/register-child/')
 */
function clearFormBackup(formUrlPath) {
    for (let i = localStorage.length - 1; i >= 0; i--) {
        const key = localStorage.key(i);
        

        if (key && key.startsWith(`form_backup_${formUrlPath}`)) {
            localStorage.removeItem(key);
        }
    }
}

/**
 * Clear all form backups for the current page
 */
function clearCurrentPageFormBackups() {
    const currentPath = window.location.pathname;
    clearFormBackup(currentPath);
}