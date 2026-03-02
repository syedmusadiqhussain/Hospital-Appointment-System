import sqlite3
import csv
import os
import random
import string
from datetime import datetime, timedelta

DB_NAME = "sehatbook.db"

def create_connection():
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
    except sqlite3.Error as e:
        print(e)
    return conn

def create_tables(conn):
    cursor = conn.cursor()
    
    # Doctors table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS doctors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        specialization TEXT,
        hospital TEXT,
        phone TEXT,
        city TEXT,
        fee_pkr INTEGER,
        availability TEXT,
        rating REAL,
        experience TEXT,
        source TEXT
    );
    """)
    
    # Slots table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS slots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doctor_id INTEGER,
        slot_date TEXT,
        slot_time TEXT,
        is_booked INTEGER DEFAULT 0,
        FOREIGN KEY (doctor_id) REFERENCES doctors (id)
    );
    """)
    
    # Appointments table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        confirmation_code TEXT UNIQUE,
        patient_name TEXT,
        patient_phone TEXT,
        patient_email TEXT,
        doctor_id INTEGER,
        slot_id INTEGER,
        reason TEXT,
        status TEXT DEFAULT 'confirmed',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (doctor_id) REFERENCES doctors (id),
        FOREIGN KEY (slot_id) REFERENCES slots (id)
    );
    """)
    
    conn.commit()

def clean_fee(fee_str):
    if not fee_str:
        return 1000
    # Remove non-digits
    digits = ''.join(filter(str.isdigit, str(fee_str)))
    if digits:
        return int(digits)
    return 1000

def insert_doctors(conn, filename, source_name):
    if not os.path.exists(filename):
        print(f"File {filename} not found, skipping.")
        return 0

    cursor = conn.cursor()
    count = 0
    
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Map columns based on source
            if 'doctors_scraped' in filename:
                name = row.get('full_name')
                spec = row.get('specialization')
                hosp = row.get('hospital')
                city = row.get('city')
                phone = row.get('phone')
                fee = clean_fee(row.get('fee'))
                rating = row.get('rating')
                exp = row.get('experience_years')
                avail = "Available Today" # Default
            else:
                name = row.get('name')
                spec = row.get('specialization')
                hosp = row.get('hospital')
                city = row.get('city')
                phone = row.get('phone_number')
                fee = clean_fee(row.get('consultation_fee'))
                rating = row.get('rating')
                exp = row.get('experience')
                avail = row.get('wait_time', 'Available Today')

            # Defaults
            if not rating: rating = 4.0
            else: rating = float(rating)
            
            if not exp: exp = "5 Years"
            else: 
                if "Years" not in str(exp) and str(exp).isdigit():
                    exp = f"{exp} Years"

            if not city and hosp:
                # Simple heuristic
                if "Lahore" in hosp: city = "Lahore"
                elif "Karachi" in hosp: city = "Karachi"
                elif "Islamabad" in hosp: city = "Islamabad"
                elif "Peshawar" in hosp: city = "Peshawar"
            
            if not city: city = "Unknown"

            # Insert
            cursor.execute("""
            INSERT INTO doctors (name, specialization, hospital, phone, city, fee_pkr, availability, rating, experience, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, spec, hosp, phone, city, fee, avail, rating, exp, source_name))
            count += 1
            
    conn.commit()
    print(f"Loaded {count} doctors from {filename}")
    return count

def generate_slots(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM doctors")
    doctors = cursor.fetchall()
    
    slot_times = ["09:00", "10:00", "11:00", "12:00", "14:00", "15:00", "16:00"]
    total_slots = 0
    
    today = datetime.now().date()
    
    for doctor in doctors:
        doc_id = doctor['id']
        # Generate for next 14 days
        for i in range(14):
            day = today + timedelta(days=i)
            date_str = day.strftime("%Y-%m-%d")
            
            for time in slot_times:
                cursor.execute("INSERT INTO slots (doctor_id, slot_date, slot_time) VALUES (?, ?, ?)", 
                               (doc_id, date_str, time))
                total_slots += 1
                
    conn.commit()
    return total_slots

def print_summary(conn):
    cursor = conn.cursor()
    
    # Total doctors
    cursor.execute("SELECT COUNT(*) as count FROM doctors")
    total_docs = cursor.fetchone()['count']
    
    # Total slots
    cursor.execute("SELECT COUNT(*) as count FROM slots")
    total_slots = cursor.fetchone()['count']
    
    print(f"\n--- Database Summary ---")
    print(f"Total doctors loaded: {total_docs}")
    print(f"Total slots created: {total_slots}")
    
    # By City
    print("\nDoctors by city:")
    cursor.execute("SELECT city, COUNT(*) as count FROM doctors GROUP BY city ORDER BY count DESC")
    for row in cursor.fetchall():
        print(f"  {row['city']}: {row['count']}")
        
    # Top Specializations
    print("\nTop 10 specializations:")
    cursor.execute("SELECT specialization, COUNT(*) as count FROM doctors GROUP BY specialization ORDER BY count DESC LIMIT 10")
    for row in cursor.fetchall():
        print(f"  {row['specialization']}: {row['count']}")

def main():
    # Check if DB exists and has data
    if os.path.exists(DB_NAME):
        conn = create_connection()
        try:
            count = conn.execute("SELECT COUNT(*) as c FROM doctors").fetchone()['c']
            if count > 0:
                print("Database already loaded.")
                conn.close()
                return
        except:
            pass # Tables might not exist
        conn.close()

    conn = create_connection()
    if conn:
        create_tables(conn)
        
        # Load from multiple files to get best data
        # Prioritize scraped data
        insert_doctors(conn, "doctors_scraped.csv", "Scraper")
        insert_doctors(conn, "all_pakistan_doctors.csv", "CSV_All")
        insert_doctors(conn, "pakistan_doctors_comprehensive.csv", "CSV_Comp")
        
        slots_count = generate_slots(conn)
        print_summary(conn)
        conn.close()

if __name__ == "__main__":
    main()
