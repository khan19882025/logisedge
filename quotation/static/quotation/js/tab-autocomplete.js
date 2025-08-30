// Tab Key Auto-Complete for Quotation Items

document.addEventListener('DOMContentLoaded', function() {
    initTabAutoComplete();
});

function initTabAutoComplete() {
    const itemsContainer = document.getElementById('items-container');
    if (!itemsContainer) return;
    
    // Handle Tab key on unit price field to add new row
    itemsContainer.addEventListener('keydown', function(e) {
        if (e.key === 'Tab' && e.target.name && e.target.name.includes('unit_price')) {
            console.log('Tab pressed on unit price field'); // Debug log
            
            // Check if this is the last unit price field
            const currentForm = e.target.closest('.item-form');
            const allForms = itemsContainer.querySelectorAll('.item-form');
            const currentIndex = Array.from(allForms).indexOf(currentForm);
            const isLastForm = currentIndex === allForms.length - 1;
            
            console.log('Current form index:', currentIndex, 'Total forms:', allForms.length, 'Is last:', isLastForm); // Debug log
            
            // If this is the last form, add new row
            if (isLastForm) {
                e.preventDefault(); // Prevent default tab behavior
                console.log('Adding new item...'); // Debug log
                
                // Call the addNewItem function if it exists
                if (typeof addNewItem === 'function') {
                    addNewItem();
                } else {
                    // Fallback: manually add new item
                    addNewItemManually();
                }
                
                // Focus on the service field of the new row
                setTimeout(() => {
                    const newForm = itemsContainer.lastElementChild;
                    const newServiceField = newForm.querySelector('select[name*="service"]');
                    if (newServiceField) {
                        newServiceField.focus();
                        console.log('Focused on new service field'); // Debug log
                    }
                }, 100);
            }
        }
    });
}

function addNewItemManually() {
    const itemsContainer = document.getElementById('items-container');
    const totalForms = document.getElementById('id_quotationitem_set-TOTAL_FORMS');
    const formNum = parseInt(totalForms.value);
    
    // Clone the first item form
    const firstForm = itemsContainer.querySelector('.item-form');
    const newForm = firstForm.cloneNode(true);
    
    // Update form indices
    newForm.innerHTML = newForm.innerHTML.replace(/quotationitem_set-\d+/g, `quotationitem_set-${formNum}`);
    
    // Clear form values
    newForm.querySelectorAll('input, select, textarea').forEach(field => {
        if (field.type === 'checkbox') {
            field.checked = false;
        } else {
            field.value = '';
        }
    });
    
    // Add delete checkbox
    const deleteCheckbox = newForm.querySelector('input[name*="DELETE"]');
    if (deleteCheckbox) {
        deleteCheckbox.checked = false;
    }
    
    // Append new form
    itemsContainer.appendChild(newForm);
    
    // Update total forms count
    totalForms.value = formNum + 1;
    
    // Recalculate totals if function exists
    if (typeof calculateTotals === 'function') {
        calculateTotals();
    }
} 