# db.py
import sqlite3
import pandas as pd
import os

DB_PATH = 'database/fraud_db.sqlite'

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs('database', exist_ok=True)
    
    # Delete old database and recreate fresh
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    conn = get_connection()

    # Load claims CSV
    df_claims = pd.read_csv('data/insurance_fraud_dataset.csv')
    df_policies = pd.read_csv('data/policies.csv')

    # Save to SQLite
    df_claims.to_sql('claims', conn, if_exists='replace', index=False)
    df_policies.to_sql('policies', conn, if_exists='replace', index=False)

    conn.commit()
    conn.close()

    print(f"Loaded {len(df_claims)} claims into database ")
    print(f"Loaded {len(df_policies)} policies into database ")

def get_claim(claim_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM claims WHERE claim_id = ?', (int(claim_id),))
    claim = cursor.fetchone()
    conn.close()
    return claim

def get_policy(policy_number):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM policies WHERE policy_number = ?', (policy_number,))
    policy = cursor.fetchone()
    conn.close()
    return policy

def get_policy_claims(policy_number):
    """Get all past claims for a policy"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM claims 
        WHERE policy_number = ?
        ORDER BY treatment_date DESC
    ''', (policy_number,))
    claims = cursor.fetchall()
    conn.close()
    return claims

def get_policy_by_number(policy_number):
    
    conn = get_connection()
    cursor = conn.cursor()

    # Get policy info
    cursor.execute('SELECT * FROM policies WHERE policy_number = ?', (policy_number,))
    policy = cursor.fetchone()

    if not policy:
        conn.close()
        return None, None

    # Get claim history
    cursor.execute('''
        SELECT * FROM claims 
        WHERE policy_number = ?
        ORDER BY treatment_date DESC
    ''', (policy_number,))
    past_claims = cursor.fetchall()
    conn.close()

    return policy, past_claims

def save_new_claim(claim_data):
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO claims (
            policy_number, patient_name, patient_age,
            hospital_name, diagnosis_type,
            claim_amount, hospital_stay_days,
            num_procedures, num_diagnoses,
            doctor_experience_years, num_claims_last_year,
            policy_age_months, claim_to_premium_ratio,
            is_duplicate_claim, treatment_date,
            monthly_premium, Class
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        claim_data['policy_number'],
        claim_data['patient_name'],
        claim_data['patient_age'],
        claim_data['hospital_name'],
        claim_data['diagnosis_type'],
        claim_data['claim_amount'],
        claim_data['hospital_stay_days'],
        claim_data['num_procedures'],
        claim_data['num_diagnoses'],
        claim_data['doctor_experience_years'],
        claim_data['num_claims_last_year'],
        claim_data['policy_age_months'],
        claim_data['claim_to_premium_ratio'],
        claim_data['is_duplicate_claim'],
        claim_data['treatment_date'],
        claim_data['monthly_premium'],
        claim_data['verdict']
    ))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

def get_stats():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as total FROM claims')
    total = cursor.fetchone()['total']
    cursor.execute('SELECT COUNT(*) as fraud FROM claims WHERE Class = 1')
    fraud = cursor.fetchone()['fraud']
    cursor.execute('SELECT COUNT(*) as policies FROM policies')
    policies = cursor.fetchone()['policies']
    conn.close()
    return {'total': total, 'fraud': fraud, 
            'legit': total - fraud, 'policies': policies}

if __name__ == "__main__":
    init_db()
    stats = get_stats()
    print(f"Total claims: {stats['total']}")
    print(f"Fraud claims: {stats['fraud']}")
    print(f"Legit claims: {stats['legit']}")
    print(f"Total policies: {stats['policies']}")