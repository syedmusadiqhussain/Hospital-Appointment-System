import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
import random
import re
import os

# Configuration
URLS = [
    "https://www.marham.pk/doctors/lahore/general-physician",
    "https://www.marham.pk/doctors/karachi/cardiologist",
    "https://www.marham.pk/doctors/islamabad/dermatologist",
    "https://www.marham.pk/doctors/peshawar/gynecologist",
    "https://www.marham.pk/doctors/lahore/pediatrician",
    "https://www.marham.pk/doctors/karachi/neurologist",
    "https://www.marham.pk/doctors/islamabad/orthopedic-surgeon",
    "https://www.marham.pk/doctors/lahore/psychiatrist",
    "https://www.marham.pk/doctors/karachi/dentist",
    "https://www.marham.pk/doctors/islamabad/ent-specialist"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.marham.pk/"
}

def extract_number(text):
    if not text:
        return ""
    # Extract digits
    nums = re.findall(r'\d+', text)
    if nums:
        return nums[0]
    return ""

def clean_fee(text):
    if not text:
        return ""
    # Extract first number sequence
    match = re.search(r'\d+', text)
    if match:
        return match.group(0)
    return ""

def scrape_doctors():
    all_doctors = []

    for url in URLS:
        print(f"Scraping {url}...")
        try:
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Extract JSON-LD data
            json_data_map = {}
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    # Handle if data is a list
                    if isinstance(data, list):
                        items = data
                    else:
                        items = [data]
                    
                    for item in items:
                        if item.get('@type') == 'Physician':
                            doc_url = item.get('url', '')
                            if doc_url:
                                json_data_map[doc_url] = item
                except:
                    continue
            
            # Find doctor cards in HTML
            # We look for the profile link class
            profile_links = soup.find_all('a', class_='dr_profile_opened_from_listing')
            
            # Use a set to track processed URLs to avoid duplicates in case of multiple links per card
            processed_urls = set()

            for link in profile_links:
                profile_url = link.get('href')
                name = link.get_text(strip=True)
                
                if not profile_url:
                    continue
                
                # Skip image links (empty text) or unrelated links
                if not name:
                    continue

                if profile_url in processed_urls:
                    continue
                
                processed_urls.add(profile_url)
                
                # Clean name
                name = re.sub(r'(?i)pmdc verified', '', name).strip()

                # Find the container card (go up to the row/card-body level)
                # Structure: div > div > a.dr_profile_opened_from_listing
                container = link.find_parent('div', class_='col-9') or link.find_parent('div', class_='row') or link.find_parent('div', class_='card-body')
                if not container:
                    container = link.find_parent('div').find_parent('div')

                # Extract HTML Data
                name = link.get_text(strip=True)
                
                # Experience
                experience = "0"
                exp_elem = container.find(string=re.compile("Experience"))
                if exp_elem:
                    # Look for the value in the next paragraph or sibling
                    parent = exp_elem.find_parent('div') or exp_elem.find_parent('p').find_parent('div')
                    if parent:
                        # Try to find the bold text in this parent
                        val_elem = parent.find('p', class_='text-bold')
                        if val_elem:
                            experience = extract_number(val_elem.get_text(strip=True))
                
                # Rating (Satisfaction)
                rating = "0"
                sat_elem = container.find(string=re.compile("Satisfaction"))
                if sat_elem:
                    parent = sat_elem.find_parent('div') or sat_elem.find_parent('p').find_parent('div')
                    if parent:
                        val_elem = parent.find('p', class_='text-bold')
                        if val_elem:
                            rating = extract_number(val_elem.get_text(strip=True)) # Extract 95 from 95%

                # Get JSON-LD data
                json_doc = json_data_map.get(profile_url, {})
                
                # Specialization
                specialization = ""
                if 'medicalSpecialty' in json_doc:
                    spec_data = json_doc['medicalSpecialty']
                    if isinstance(spec_data, dict):
                        specialization = spec_data.get('name', '')
                    elif isinstance(spec_data, str):
                        specialization = spec_data
                    elif isinstance(spec_data, list):
                         specialization = ", ".join([s.get('name', '') if isinstance(s, dict) else str(s) for s in spec_data])
                
                if not specialization:
                    # Try HTML
                    # Usually <p class="mb-0 mt-10 text-sm">Spec 1, Spec 2</p>
                    # It's usually the p tag after the name div
                    try:
                        spec_p = link.find_parent('div').find_next_sibling('p')
                        if spec_p:
                            specialization = spec_p.get_text(strip=True)
                    except:
                        pass

                # Fee
                fee = "0"
                if 'priceRange' in json_doc:
                    fee = clean_fee(json_doc['priceRange'])
                
                # Hospital
                hospital = ""
                city = ""
                # Infer city from URL if not found
                url_parts = url.split('/')
                if len(url_parts) > 4:
                    city_from_url = url_parts[4].capitalize()
                    city = city_from_url

                if 'hospitalAffiliation' in json_doc:
                    hospitals = json_doc['hospitalAffiliation']
                    if isinstance(hospitals, list) and len(hospitals) > 0:
                        hospital = hospitals[0].get('name', '')
                        address = hospitals[0].get('address', {})
                        if isinstance(address, dict):
                            city_json = address.get('addressLocality') or address.get('addressRegion')
                            if city_json and city_json.lower() != "online":
                                city = city_json

                # Phone
                phone = ""
                if 'telephone' in json_doc:
                    phone = json_doc['telephone']
                
                # If phone is landline or missing, we can try to find other sources or keep it.
                # User requested 03XX format. If we only have landline, we keep it but maybe it's not what they want.
                # Marham usually masks real numbers. 
                # We will check if we found a mobile number.
                
                doctor_data = {
                    "full_name": name,
                    "specialization": specialization,
                    "fee": fee,
                    "hospital": hospital,
                    "city": city,
                    "phone": phone,
                    "experience_years": experience,
                    "rating": rating,
                    "profile_url": profile_url
                }
                
                all_doctors.append(doctor_data)
                
            time.sleep(random.uniform(2, 4))
            
        except Exception as e:
            print(f"Error scraping {url}: {e}")

    return all_doctors

def save_data(doctors):
    if not doctors:
        print("No doctors found.")
        return

    # Save CSV
    df = pd.DataFrame(doctors)
    df.to_csv("doctors_scraped.csv", index=False)
    print("Saved doctors_scraped.csv")

    # Save JSON
    with open("doctors_scraped.json", "w", encoding="utf-8") as f:
        json.dump(doctors, f, indent=2, ensure_ascii=False)
    print("Saved doctors_scraped.json")

    # Save SQL
    with open("doctors_insert.sql", "w", encoding="utf-8") as f:
        for doc in doctors:
            # Escape single quotes
            name = doc['full_name'].replace("'", "''")
            spec = doc['specialization'].replace("'", "''")
            hosp = doc['hospital'].replace("'", "''")
            city = doc['city'].replace("'", "''")
            
            # Handle numeric fields
            fee = doc['fee'] if doc['fee'] else '0'
            exp = doc['experience_years'] if doc['experience_years'] else '0'
            rating = doc['rating'] if doc['rating'] else '0'
            
            sql = f"INSERT INTO doctors (full_name, specialization, fee, hospital_name, city, phone_number, experience_years, rating, profile_url) VALUES ('{name}', '{spec}', {fee}, '{hosp}', '{city}', '{doc['phone']}', {exp}, {rating}, '{doc['profile_url']}');\n"
            f.write(sql)
    print("Saved doctors_insert.sql")

def print_summary(doctors):
    print("\n--- Summary ---")
    print(f"Total doctors found: {len(doctors)}")
    
    phone_count = sum(1 for d in doctors if d['phone'])
    print(f"How many have phone numbers: {phone_count}")
    
    df = pd.DataFrame(doctors)
    if not df.empty:
        print("\nCount by city:")
        print(df['city'].value_counts().to_string())
        
        # Simplify specialization for counting (take first one)
        print("\nCount by specialty (top 5):")
        # Split by comma and explode? Or just use raw string
        print(df['specialization'].value_counts().head(5).to_string())

if __name__ == "__main__":
    doctors = scrape_doctors()
    save_data(doctors)
    print_summary(doctors)
