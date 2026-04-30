
function fillSample(type) {
    if (type === 'legit') {
        document.getElementById('patient_name').value = 'Priya Mehta';
        document.getElementById('patient_age').value = '42';
        document.getElementById('policy_number').value = 'LIC-2019-4521';
        document.getElementById('hospital_name').value = 'Apollo Hospital, Mumbai';
        document.getElementById('diagnosis').value = 'Appendectomy';
        document.getElementById('claim_amount').value = '85000';
        document.getElementById('hospital_stay_days').value = '3';
        document.getElementById('treatment_date').value = '2026-03-15';
    } else {
        document.getElementById('patient_name').value = 'Ramesh Gupta';
        document.getElementById('patient_age').value = '38';
        document.getElementById('policy_number').value = 'LIC-2025-0023';
        document.getElementById('hospital_name').value = 'Care Hospital, Delhi';
        document.getElementById('diagnosis').value = 'Multiple Organ Treatment';
        document.getElementById('claim_amount').value = '980000';
        document.getElementById('hospital_stay_days').value = '22';
        document.getElementById('treatment_date').value = '2026-01-10';
    }
}

async function predict() {
    
    const required = ['patient_name', 'patient_age', 'policy_number',
                      'hospital_name', 'diagnosis', 'claim_amount',
                      'hospital_stay_days', 'treatment_date'];
    
    for (let field of required) {
        if (!document.getElementById(field).value) {
            alert('Please fill all fields before analyzing!');
            return;
        }
    }

    const btn = document.querySelector('.predict-btn');
    btn.disabled = true;
    btn.textContent = ' Analyzing Claim...';

    document.getElementById('result').innerHTML = `
        <div class="loading-card">
             Running AI fraud detection models...<br>
            <small style="color:#555; margin-top:8px; display:block">
                Checking claim history, procedures, policy age...
            </small>
        </div>`;

    const data = {
        patient_name: document.getElementById('patient_name').value,
        patient_age: +document.getElementById('patient_age').value,
        policy_number: document.getElementById('policy_number').value,
        hospital_name: document.getElementById('hospital_name').value,
        diagnosis: document.getElementById('diagnosis').value,
        claim_amount: +document.getElementById('claim_amount').value,
        hospital_stay_days: +document.getElementById('hospital_stay_days').value,
        treatment_date: document.getElementById('treatment_date').value
    };

    try {
        const res = await fetch('/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await res.json();
        const isFraud = result.final_verdict === 'FRAUD';
        const h = result.history;

        document.getElementById('result').innerHTML = `
            <div class="result-card">

                <div class="verdict-banner ${isFraud ? 'fraud' : 'legit'}">
                    <h2>${isFraud ? ' FRAUD DETECTED' : ' LEGITIMATE CLAIM'}</h2>
                    <p>${isFraud 
                        ? 'This claim has been flagged as potentially fraudulent. Please escalate for manual review.' 
                        : 'This claim appears legitimate. You may proceed with approval.'}</p>
                </div>

                <div class="risk-meter">
                    <label>Fraud Risk Score: ${result.fraud_score}%</label>
                    <div class="meter-bar">
                        <div class="meter-fill ${isFraud ? 'high' : 'low'}" 
                             style="width: ${result.fraud_score}%">
                        </div>
                    </div>
                    <div class="meter-pct">${result.fraud_score}% risk</div>
                </div>

                <div class="model-results">
                    <div class="model-card">
                        <div class="model-name"> Autoencoder</div>
                        <div class="model-verdict ${result.autoencoder === 'FRAUD' ? 'fraud' : 'legit'}">
                            ${result.autoencoder === 'FRAUD' ? 'FRAUD' : ' LEGIT'}
                        </div>
                    </div>
                    <div class="model-card">
                        <div class="model-name"> Isolation Forest</div>
                        <div class="model-verdict ${result.isolation_forest === 'FRAUD' ? 'fraud' : 'legit'}">
                            ${result.isolation_forest === 'FRAUD' ? ' FRAUD' : 'LEGIT'}
                        </div>
                    </div>
                    <div class="model-card">
                        <div class="model-name"> XGBoost</div>
                        <div class="model-verdict ${result.xgboost === 'FRAUD' ? 'fraud' : 'legit'}">
                            ${result.xgboost === 'FRAUD' ? ' FRAUD' : ' LEGIT'}
                        </div>
                    </div>
                </div>

                <div class="flags-section">
                    <h4>🔎 System Detected Flags (Auto-pulled from Database)</h4>
                    <div class="flags-grid">
                        <div class="flag-item">
                            <span>Claims Last Year</span>
                            <span style="color: ${h.num_claims_last_year > 5 ? '#e74c3c' : '#2ecc71'}">
                                ${h.num_claims_last_year}
                            </span>
                        </div>
                        <div class="flag-item">
                            <span>Policy Age</span>
                            <span style="color: ${h.policy_age_months < 6 ? '#e74c3c' : '#2ecc71'}">
                                ${h.policy_age_months} months
                            </span>
                        </div>
                        <div class="flag-item">
                            <span>Duplicate Claim</span>
                            <span style="color: ${h.is_duplicate_claim ? '#e74c3c' : '#2ecc71'}">
                                ${h.is_duplicate_claim ? 'YES ' : 'NO '}
                            </span>
                        </div>
                        <div class="flag-item">
                            <span>Approved Quickly</span>
                            <span style="color: ${h.claim_approved_quickly ? '#e74c3c' : '#2ecc71'}">
                                ${h.claim_approved_quickly ? 'YES ' : 'NO '}
                            </span>
                        </div>
                        <div class="flag-item">
                            <span>Num Procedures</span>
                            <span style="color: ${h.num_procedures > 8 ? '#e74c3c' : '#2ecc71'}">
                                ${h.num_procedures}
                            </span>
                        </div>
                        <div class="flag-item">
                            <span>Reconstruction Error</span>
                            <span style="color: ${result.reconstruction_error > 2.5 ? '#e74c3c' : '#2ecc71'}">
                                ${result.reconstruction_error}
                            </span>
                        </div>
                    </div>
                </div>

            </div>`;

    } catch (err) {
        document.getElementById('result').innerHTML = `
            <div class="result-card">
                <div class="verdict-banner fraud">
                    <h2> Error</h2>
                    <p>${err.message}</p>
                </div>
            </div>`;
    } finally {
        btn.disabled = false;
        btn.textContent = ' Analyze Claim for Fraud';
    }
}