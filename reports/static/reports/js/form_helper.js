/**
 * Form Helper Script for Developer Testing
 * Usage: click the hidden/dev button or run fillDevData() in console.
 */

function fillDevData() {
    console.log("Filling form with dev data...");
    
    // Helpers
    const setVal = (name, val) => {
        const els = document.querySelectorAll(`[name="${name}"]`);
        els.forEach(el => {
            if (el.type === 'radio' && el.value === val) el.checked = true;
            else if (el.type === 'checkbox') el.checked = val === true;
            else el.value = val;
        });
    };

    // 1. Dates
    setVal('registration_date', '2024-01-01');
    setVal('start_date', '2024-02-01');

    // 2. Identity
    setVal('child_first_name', 'Arthur');
    setVal('child_last_name', 'Pendragon');
    setVal('child_gender', 'masculin');
    setVal('birth_date', '2020-05-15');
    setVal('medicare_number', 'PEND 1234 5678');
    setVal('medicare_expiry', '2028-05-15');

    // 3. Address
    setVal('addr_street', '123 Camelot Castle Way');
    setVal('addr_apt', 'King Suite');
    setVal('addr_city', 'Avalon');
    setVal('addr_prov', 'QC');
    setVal('addr_zip', 'H0H 0H0');

    // 4. Parents
    setVal('parent1_name', 'Uther Pendragon');
    setVal('parent1_email', 'uther@kingdom.com');
    setVal('parent1_home_phone', '514-555-0101');
    setVal('parent1_workplace', 'Royal Court');
    setVal('parent1_work_phone', '514-555-0102');
    setVal('parent1_cell_phone', '514-555-0103');
    // Parent 1 Address
    setVal('parent1_address_street', '123 Camelot Castle Way');
    setVal('parent1_address_city', 'Avalon');

    setVal('parent2_name', 'Igraine Pendragon');
    setVal('parent2_email', 'igraine@kingdom.com');
    setVal('parent2_home_phone', '514-555-0201');
    setVal('parent2_workplace', 'Royal Court');
    setVal('parent2_cell_phone', '514-555-0203');

    // Custody
    setVal('custody_arrangement', 'Joint Custody');

    // Pickups (Array handling)
    const pickupNames = document.querySelectorAll('[name="pickup_name[]"]');
    if(pickupNames[0]) {
        pickupNames[0].value = "Merlin The Wizard";
        document.querySelectorAll('[name="pickup_rel[]"]')[0].value = "Advisor";
        document.querySelectorAll('[name="pickup_phone[]"]')[0].value = "555-MAGIC";
        document.querySelectorAll('[name="pickup_addr[]"]')[0].value = "Tower 1";
    }

    // Emergency
    const emergNames = document.querySelectorAll('[name="emerg_name[]"]');
    if(emergNames[0]) {
        emergNames[0].value = "Lancelot Du Lac";
        document.querySelectorAll('[name="emerg_phone[]"]')[0].value = "555-SWORD";
        document.querySelectorAll('[name="emerg_rel[]"]')[0].value = "Knight";
    }

    // Medical
    setVal('doctor_name', 'Gaius');
    setVal('doctor_phone', '555-HEAL');
    setVal('doctor_address', 'Lower Town, Camelot');
    
    // Allergies (Dynamic)
    if (typeof addAllergyRow === 'function') {
        const container = document.getElementById('allergies-container');
        // Clear first if needed or just add
        const existing = container.querySelectorAll('input');
        if (existing.length === 1 && existing[0].value === '') {
            existing[0].value = "Dragon Breath";
        } else {
            addAllergyRow("Dragon Breath");
        }
        addAllergyRow("Dark Magic");
    }

    setVal('non_fatal_allergies', 'Pollen, Magic Dust');
    setVal('requires_epipen', 'non');
    setVal('dietary_restrictions', 'Lactose Intolerant');
    setVal('cultural_dietary_restrictions', 'No Pork (Knight Diet)');
    
    setVal('routine_services_required', 'on');
    setVal('routine_services_details', 'Daily potion at noon');
    setVal('continuous_medication', 'Strength elixir');
    setVal('activity_restrictions', 'No flying without supervision');
    
    // Medical History
    const diseases = ['measles', 'mumps', 'rubella', 'chickenpox'];
    diseases.forEach(d => {
        setVal(`${d}_medical_history`, 'non');
    });

    // Development
    setVal('preschool_history', 'Merlin School of Wizardry');
    setVal('preschool_duration', '2 years');
    
    setVal('autonomy_dressing', 'Needs help with armor');
    setVal('autonomy_eating', 'Uses spoon well');
    setVal('autonomy_toilet', 'Potty trained');
    setVal('autonomy_hygiene', 'Loves baths');
    setVal('motor_skills', 'Excellent sword handling (plastic), good climbing');
    
    setVal('transition_tips', 'Likes stories about swords.');
    setVal('interests_hobbies', 'Horse riding, sword fighting.');
    setVal('additional_info', 'Afraid of Morgana');

    // Immunization
    setVal('immunization_provided', true);

    console.log("Dev data filled!");
}