from firecrawl import Firecrawl
import pandas as pd
import json
import time
import os

def scrape_doctors_by_city_and_specialty():
    api_key = "fc-b06a2507bcd8448bbf8c64c69c178a98"
    app = Firecrawl(api_key=api_key)
    
    # Define cities and specialties
    cities = ['lahore', 'karachi', 'islamabad']
    specialties = ['cardiologist', 'dermatologist', 'gynecologist']
    
    all_doctors = []
    
    # Define schema
    schema = {
        "type": "object",
        "properties": {
            "doctors": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "specialization": {"type": "string"},
                        "hospital": {"type": "string"},
                        "phone_number": {"type": "string"},
                        "location": {"type": "string"},
                        "consultation_fee": {"type": "string"},
                        "wait_time": {"type": "string"}
                    },
                    "required": ["name", "specialization", "hospital", "location"]
                }
            }
        },
        "required": ["doctors"]
    }
    
    for city in cities:
        for specialty in specialties:
            url = f"https://www.marham.pk/doctors/{city}/{specialty}"
            print(f"\nScraping {specialty}s in {city.capitalize()} from {url}...")
            
            try:
                # Use v1 scrape_url as it worked before
                if hasattr(app, 'v1') and app.v1:
                    result = app.v1.scrape_url(
                        url, 
                        formats=['extract'],
                        extract={
                            'schema': schema
                        },
                        timeout=120000
                    )
                else:
                     result = app.scrape_url(
                        url, 
                        formats=['extract'],
                        extract={
                            'schema': schema
                        },
                        timeout=120000
                    )
                
                # Check result structure
                data = None
                if hasattr(result, 'extract'):
                    data = result.extract
                elif isinstance(result, dict) and 'extract' in result:
                    data = result['extract']
                elif isinstance(result, dict) and 'data' in result and 'extract' in result['data']:
                    data = result['data']['extract']
                    
                if data and 'doctors' in data:
                    doctors = data['doctors']
                    print(f"Successfully extracted {len(doctors)} doctors.")
                    # Add metadata
                    for doc in doctors:
                        doc['city'] = city.capitalize()
                        doc['category'] = specialty.capitalize()
                    all_doctors.extend(doctors)
                else:
                    print(f"No doctor data found for {city}/{specialty}. Result: {data}")
                    
            except Exception as e:
                print(f"Error scraping {city}/{specialty}: {e}")
                
            # Be polite to the server
            time.sleep(2)
    
    # Save all data to CSV
    if all_doctors:
        df = pd.DataFrame(all_doctors)
        output_file = 'pakistan_doctors_comprehensive.csv'
        df.to_csv(output_file, index=False)
        print(f"\nTotal {len(all_doctors)} doctors scraped.")
        print(f"Data saved to {output_file}")
        print(df.head())
    else:
        print("No doctors scraped.")

if __name__ == "__main__":
    scrape_doctors_by_city_and_specialty()
