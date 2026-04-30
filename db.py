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
    conn = get_connection()
    cursor = conn.cursor()

    # Create claims table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS claims (
            claim_id INTEGER PRIMARY KEY,
            patient_age INTEGER,
            claim_amount REAL,
            num_procedures INTEGER,
            hospital_stay_days INTEGER,
            num_claims_last_year INTEGER,
            doctor_experience_years INTEGER,
            is_duplicate_claim INTEGER,
            claim_approved_quickly INTEGER,
            num_diagnoses INTEGER,
            patient_income_level INTEGER,
            policy_age_months INTEGER,
            Class INTEGER
        )
    ''')

    csv_path = 'data/insurance_fraud_dataset.csv'
    df = pd.read_csv(csv_path)
    df['claim_id'] = df['claim_id'].astype(int)
    df['Class'] = df['Class'].astype(int)

    df.to_sql('claims', conn, if_exists='replace', index=False)
    print(f"Loaded {len(df)} claims into database ")

    conn.commit()
    conn.close()

def get_claim(claim_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM claims WHERE claim_id = ?', (int(claim_id),))
    claim = cursor.fetchone()
    conn.close()
    return claim

def get_similar_claims(claim_id, limit=5):
    
    conn = get_connection()
    cursor = conn.cursor()
    claim = get_claim(claim_id)
    if claim:
        age = claim['patient_age']
        cursor.execute('''
            SELECT * FROM claims 
            WHERE patient_age BETWEEN ? AND ?
            AND claim_id != ?
            ORDER BY RANDOM()
            LIMIT ?
        ''', (age-5, age+5, claim_id, limit))
    results = cursor.fetchall()
    conn.close()
    return results

def save_new_claim(claim_data):
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO claims (
            patient_age, claim_amount, num_procedures,
            hospital_stay_days, num_claims_last_year,
            doctor_experience_years, is_duplicate_claim,
            claim_approved_quickly, num_diagnoses,
            patient_income_level, policy_age_months, Class
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        claim_data['patient_age'],
        claim_data['claim_amount'],
        claim_data['num_procedures'],
        claim_data['hospital_stay_days'],
        claim_data['num_claims_last_year'],
        claim_data['doctor_experience_years'],
        claim_data['is_duplicate_claim'],
        claim_data['claim_approved_quickly'],
        claim_data['num_diagnoses'],
        claim_data['patient_income_level'],
        claim_data['policy_age_months'],
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
    conn.close()
    return {'total': total, 'fraud': fraud, 'legit': total - fraud}

if __name__ == "__main__":
    init_db()
    stats = get_stats()
    print(f"Total claims: {stats['total']}")
    print(f"Fraud claims: {stats['fraud']}")
    print(f"Legit claims: {stats['legit']}")