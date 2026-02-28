import pandas as pd
import sqlite3
import os

def setup_database():
    db_file = 'hospital_appointment.db'
    
    # List of CSV files to consolidate
    csv_files = [
        'pakistan_doctors_comprehensive.csv',
        'peshawar_doctors.csv',
        'all_pakistan_doctors.csv',
        'doctors_firecrawl.csv'
    ]
    
    all_data = []
    
    for file in csv_files:
        if os.path.exists(file):
            print(f"Reading {file}...")
            try:
                df = pd.read_csv(file)
                # Standardize columns
                # Add missing columns if they don't exist
                if 'city' not in df.columns:
                    df['city'] = 'Unknown' # Or infer from location if possible
                if 'category' not in df.columns:
                    df['category'] = 'General' # Default category
                
                # For doctors_firecrawl.csv which was the first test, we know it was Cardiologists in Lahore
                if file == 'doctors_firecrawl.csv':
                    df['city'] = 'Lahore'
                    df['category'] = 'Cardiologist'
                    
                all_data.append(df)
            except Exception as e:
                print(f"Error reading {file}: {e}")
        else:
            print(f"File {file} not found.")
    
    if not all_data:
        print("No data found to import.")
        return

    # Concatenate all dataframes
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Clean up column names (strip whitespace, lower case)
    combined_df.columns = [c.strip().lower().replace(' ', '_') for c in combined_df.columns]
    
    # Drop duplicates based on name and hospital
    initial_count = len(combined_df)
    combined_df.drop_duplicates(subset=['name', 'hospital', 'location'], keep='first', inplace=True)
    final_count = len(combined_df)
    
    print(f"Consolidated {initial_count} records. Removed {initial_count - final_count} duplicates. Final count: {final_count}")
    
    # Create SQLite database
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Drop table if exists to reset
    cursor.execute("DROP TABLE IF EXISTS doctors")
    
    # Create table with explicit ID
    create_table_sql = """
    CREATE TABLE doctors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        specialization TEXT,
        hospital TEXT,
        phone_number TEXT,
        location TEXT,
        consultation_fee TEXT,
        wait_time TEXT,
        city TEXT,
        category TEXT
    );
    """
    cursor.execute(create_table_sql)
    
    # Insert data
    # Ensure columns match the table schema (except id)
    columns_to_keep = [
        'name', 'specialization', 'hospital', 'phone_number', 
        'location', 'consultation_fee', 'wait_time', 'city', 'category'
    ]
    
    # Filter columns that exist in the dataframe
    existing_columns = [col for col in columns_to_keep if col in combined_df.columns]
    final_df = combined_df[existing_columns]
    
    # Write to database using append
    final_df.to_sql('doctors', conn, if_exists='append', index=False)
    
    # Create index for faster searching
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_city ON doctors(city);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_specialization ON doctors(specialization);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON doctors(category);")
    
    conn.commit()
    conn.close()
    
    print(f"Successfully created database '{db_file}' with table 'doctors'.")
    
    # Verify
    verify_db(db_file)

def verify_db(db_file):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Check if id column exists
    cursor.execute("PRAGMA table_info(doctors)")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"Columns in 'doctors' table: {columns}")
    
    cursor.execute("SELECT COUNT(*) FROM doctors")
    count = cursor.fetchone()[0]
    print(f"Total rows in 'doctors' table: {count}")
    
    if count > 0:
        cursor.execute("SELECT * FROM doctors LIMIT 1")
        print("Sample row:", cursor.fetchone())
        
    conn.close()

if __name__ == "__main__":
    setup_database()
