// static/script.js
const claimsLog = [];
let currentPolicy = null;
let riskChart = null;

function fillPolicy(type) {
    if (type === 'legit') {
        const legitPolicies = [
            'LIC-2018-0001', 'LIC-2019-0002', 'LIC-2017-0005',
            'LIC-2020-0010', 'LIC-2016-0015'
        ];
        const p = legitPolicies[Math.floor(Math.random() * legitPolicies.length)];
        document.getElementById('policy_number').value = p;
    } else {
        const fraudPolicies = [
            'LIC-2024-0401', 'LIC-2025-0410', 'LIC-2023-0420',
            'LIC-2024-0430', 'LIC-2025-0440'
        ];
        const p = fraudPolicies[Math.floor(Math.random() * fraudPolicies.length)];
        document.getElementById('policy_number').value = p;
    }
}

async function lookupPolicy() {
    const policyNumber = document.getElementById('policy_number').value.trim();
    if (!policyNumber) {
        alert('Please enter a policy number!');
        return;
    }

    const btn = document.querySelector('.lookup-btn');
    btn.disabled = true;
    btn.textContent = '⏳ Looking up...';

    try {
        const res = await fetch('/lookup_policy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ policy_number: policyNumber })
        });

        if (res.status === 404) {
            const err = await res.json();
            alert(err.error + '\n\nTry: LIC-2018-0001 to LIC-2022-0400 for legit\nLIC-2023-0401 to LIC-2025-0500 for fraud prone');
            return;
        }

        const policy = await res.json();
        currentPolicy = policy;

        // Show policy card
        document.getElementById('policy-card').style.display = 'block';
        document.getElementById('claim-form').style.display = 'block';
        document.getElementById('result').innerHTML = '';

        // Fill policy details
        document.getElementById('policy-details').innerHTML = `
            <div class="detail-item">
                <span class="detail-label">Patient Name</span>
                <span class="detail-value">${policy.patient_name}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Patient Age</span>
                <span class="detail-value">${policy.patient_age} years</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Policy Number</span>
                <span class="detail-value">${policy.policy_number}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Policy Start Date</span>
                <span class="detail-value">${policy.policy_start_date}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Policy Age</span>
                <span class="detail-value ${policy.policy_age_months < 6 ? 'warn' : 'good'}">
                    ${policy.policy_age_months} months
                </span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Monthly Premium</span>
                <span class="detail-value">₹${Number(policy.monthly_premium).toLocaleString('en-IN')}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Coverage Amount</span>
                <span class="detail-value">₹${Number(policy.coverage_amount).toLocaleString('en-IN')}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Claims Last Year</span>
                <span class="detail-value ${policy.num_claims_last_year > 4 ? 'warn' : 'good'}">
                    ${policy.num_claims_last_year}
                </span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Total Past Claims</span>
                <span class="detail-value ${policy.total_past_claims > 6 ? 'warn' : 'good'}">
                    ${policy.total_past_claims}
                </span>
            </div>
        `;

        // Show past claims
        if (policy.past_claims && policy.past_claims.length > 0) {
            document.getElementById('past-claims-section').style.display = 'block';
            document.getElementById('past-claims-body').innerHTML =
                policy.past_claims.map(c => `
                    <tr>
                        <td>#${c.claim_id}</td>
                        <td>₹${Number(c.claim_amount).toLocaleString('en-IN')}</td>
                        <td>${c.hospital_name || 'N/A'}</td>
                        <td>${c.diagnosis_type || 'N/A'}</td>
                        <td>${c.treatment_date}</td>
                        <td>
                            <span class="badge-${c.Class === 1 ? 'fraud' : 'legit'}">
                                ${c.Class === 1 ? 'FRAUD' : 'LEGIT'}
                            </span>
                        </td>
                    </tr>
                `).join('');
        }

    } catch (err) {
        alert('Error: ' + err.message);
    } finally {
        btn.disabled = false;
        btn.textContent = '🔍 Lookup Policy';
    }
}

async function analyzeFraud() {
    if (!currentPolicy) return;

    const required = ['hospital_name', 'diagnosis_type',
                      'claim_amount', 'hospital_stay_days'];
    for (let field of required) {
        if (!document.getElementById(field).value) {
            alert('Please fill all claim details!');
            return;
        }
    }

    const btn = document.querySelector('.predict-btn');
    btn.disabled = true;
    btn.textContent = '⏳ Analyzing...';

    document.getElementById('result').innerHTML = `
        <div class="loading-card">
            🔍 Running AI fraud detection models...<br>
            <small style="color:#555; margin-top:8px; display:block">
                Calculating risk features from policy history...
            </small>
        </div>`;

    const data = {
        policy_number: currentPolicy.policy_number,
        hospital_name: document.getElementById('hospital_name').value,
        diagnosis_type: document.getElementById('diagnosis_type').value,
        claim_amount: +document.getElementById('claim_amount').value,
        hospital_stay_days: +document.getElementById('hospital_stay_days').value,
        num_diagnoses: +document.getElementById('num_diagnoses').value,
        doctor_experience_years: +document.getElementById('doctor_experience_years').value
    };

    try {
        const res = await fetch('/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await res.json();
        const isFraud = result.final_verdict === 'FRAUD';
        const d = result.derived_features;

        document.getElementById('result').innerHTML = `
            <div class="result-card">
                <div class="verdict-banner ${isFraud ? 'fraud' : 'legit'}">
                    <h2>${isFraud ? ' FRAUD DETECTED' : '✅ LEGITIMATE CLAIM'}</h2>
                    <p>${isFraud
                        ? 'This claim has been flagged as potentially fraudulent. Please escalate for manual review.'
                        : 'This claim appears legitimate. You may proceed with approval.'}</p>
                </div>

                <div class="result-body">
                    <div class="left-col">
                        <div class="risk-meter">
                            <label>Fraud Risk Score</label>
                            <div class="donut-wrap">
                                <canvas id="riskChart" width="160" height="160"></canvas>
                                <div class="donut-label">${result.fraud_score}%</div>
                            </div>
                        </div>

                        <div class="model-results">
                            <div class="model-card">
                                <div class="model-name"> Autoencoder</div>
                                <div class="model-verdict ${result.autoencoder === 'FRAUD' ? 'fraud' : 'legit'}">
                                    ${result.autoencoder === 'FRAUD' ? ' FRAUD' : ' LEGIT'}
                                </div>
                            </div>
                            <div class="model-card">
                                <div class="model-name"> Isolation Forest</div>
                                <div class="model-verdict ${result.isolation_forest === 'FRAUD' ? 'fraud' : 'legit'}">
                                    ${result.isolation_forest === 'FRAUD' ? ' FRAUD' : ' LEGIT'}
                                </div>
                            </div>
                            <div class="model-card">
                                <div class="model-name"> XGBoost</div>
                                <div class="model-verdict ${result.xgboost === 'FRAUD' ? 'fraud' : 'legit'}">
                                    ${result.xgboost === 'FRAUD' ? ' FRAUD' : ' LEGIT'}
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="right-col">
                        <div class="flags-section">
                            <h4> Auto-Calculated Risk Flags</h4>
                            <div class="flag-item">
                                <span>Claims Last Year</span>
                                <span style="color:${d.num_claims_last_year > 4 ? '#e74c3c' : '#2ecc71'}">
                                    ${d.num_claims_last_year}
                                </span>
                            </div>
                            <div class="flag-item">
                                <span>Policy Age</span>
                                <span style="color:${d.policy_age_months < 6 ? '#e74c3c' : '#2ecc71'}">
                                    ${d.policy_age_months} months
                                </span>
                            </div>
                            <div class="flag-item">
                                <span>Claim/Premium Ratio</span>
                                <span style="color:${d.claim_to_premium_ratio > 3 ? '#e74c3c' : '#2ecc71'}">
                                    ${d.claim_to_premium_ratio}x
                                </span>
                            </div>
                            <div class="flag-item">
                                <span>Duplicate Claim</span>
                                <span style="color:${d.is_duplicate ? '#e74c3c' : '#2ecc71'}">
                                    ${d.is_duplicate ? 'YES ' : 'NO '}
                                </span>
                            </div>
                            <div class="flag-item">
                                <span>Num Procedures</span>
                                <span style="color:${d.num_procedures > 8 ? '#e74c3c' : '#2ecc71'}">
                                    ${d.num_procedures}
                                </span>
                            </div>
                            <div class="flag-item">
                                <span>Reconstruction Error</span>
                                <span style="color:${result.reconstruction_error > 1.4 ? '#e74c3c' : '#2ecc71'}">
                                    ${result.reconstruction_error}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>`;

        renderChart(result.fraud_score);
        updateLog(currentPolicy.policy_number, currentPolicy.patient_name,
                  data.claim_amount, result.fraud_score, result.final_verdict);

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
        btn.textContent = ' Analyze This Claim for Fraud';
    }
}

function renderChart(fraudScore) {
    const ctx = document.getElementById('riskChart').getContext('2d');
    if (riskChart) riskChart.destroy();
    riskChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [fraudScore, 100 - fraudScore],
                backgroundColor: [
                    fraudScore > 50 ? '#e74c3c' : '#2ecc71',
                    '#1a1a2e'
                ],
                borderWidth: 0
            }]
        },
        options: {
            cutout: '75%',
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false }
            }
        }
    });
}

function updateLog(policy, patient, amount, score, verdict) {
    const now = new Date();
    claimsLog.unshift({ policy, patient, amount, score, verdict,
                        time: now.toLocaleTimeString() });

    document.getElementById('log-card').style.display = 'block';
    document.getElementById('log-body').innerHTML = claimsLog.slice(0, 10).map(c => `
        <tr>
            <td>${c.policy}</td>
            <td>${c.patient}</td>
            <td>₹${Number(c.amount).toLocaleString('en-IN')}</td>
            <td>${c.score}%</td>
            <td><span class="badge-${c.verdict === 'FRAUD' ? 'fraud' : 'legit'}">
                ${c.verdict}
            </span></td>
            <td>${c.time}</td>
        </tr>
    `).join('');
}