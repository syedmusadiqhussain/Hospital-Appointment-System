from firecrawl import Firecrawl
import pandas as pd
import json

def scrape_cities_and_specialties():
    api_key = "fc-b06a2507bcd8448bbf8c64c69c178a98"
    app = Firecrawl(api_key=api_key)
    
    url = "https://www.marham.pk/doctors"
    
    print(f"Scraping {url} using Firecrawl (v2)...")
    
    # Define the schema for extraction
    schema = {
        "type": "object",
        "properties": {
            "cities": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of cities in Pakistan where doctors are available"
            },
            "specialties": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of medical specialties"
            }
        },
        "required": ["cities", "specialties"]
    }
    
    try:
        # Try using v1 scrape_url via the v1 proxy
        if hasattr(app, 'v1') and app.v1:
            print("Using v1 scrape_url...")
            result = app.v1.scrape_url(
                url, 
                formats=['extract'],
                extract={
                    'schema': schema
                },
                timeout=120000
            )
        else:
             print("Using app.scrape_url (assuming legacy or direct v1)...")
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
            
        if data:
            print("Successfully extracted data.")
            print("Cities:", data.get('cities', [])[:10]) # Print first 10
            print("Specialties:", data.get('specialties', [])[:10]) # Print first 10
            
            # Save to JSON
            with open('marham_metadata.json', 'w') as f:
                json.dump(data, f, indent=4)
            print("Data saved to marham_metadata.json")
            
        else:
            print("Extraction failed or returned no data.")
            print(result)
            
    except Exception as e:
        print(f"Error during scraping: {e}")

if __name__ == "__main__":
    scrape_cities_and_specialties()
