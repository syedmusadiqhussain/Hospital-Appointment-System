from firecrawl import Firecrawl
import pandas as pd
import json

def scrape_with_firecrawl():
    api_key = "fc-b06a2507bcd8448bbf8c64c69c178a98"
    app = Firecrawl(api_key=api_key)
    
    url = "https://www.marham.pk/doctors/lahore/cardiologist"
    
    print(f"Scraping {url} using Firecrawl (v2)...")
    
    # Define the schema for extraction
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
             # Fallback to direct call if v1 is not exposed but maybe it's a V1FirecrawlApp instance
             # This branch is just in case
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
        # result might be an object (V1ScrapeResponse) or a dict
        data = None
        if hasattr(result, 'extract'):
            data = result.extract
        elif isinstance(result, dict) and 'extract' in result:
            data = result['extract']
        elif isinstance(result, dict) and 'data' in result and 'extract' in result['data']:
            data = result['data']['extract']
            
        if data:
            if 'doctors' in data:
                doctors = data['doctors']
                print(f"Successfully extracted {len(doctors)} doctors.")
                
                # Save to CSV
                df = pd.DataFrame(doctors)
                df.to_csv('doctors_firecrawl.csv', index=False)
                print("Data saved to doctors_firecrawl.csv")
                print(df.head())
            else:
                print("No 'doctors' key in extracted data:", data)
        else:
            print("Extraction failed or returned no data.")
            print(result)
            
    except AttributeError:
        # Fallback to .scrape if .scrape_url is not available on Firecrawl class
        try:
             result = app.scrape(
                url, 
                params={
                    'formats': ['extract'],
                    'extract': {
                        'schema': schema
                    }
                }
            )
             if 'extract' in result:
                data = result['extract']
                if 'doctors' in data:
                    doctors = data['doctors']
                    print(f"Successfully extracted {len(doctors)} doctors.")
                    df = pd.DataFrame(doctors)
                    df.to_csv('doctors_firecrawl.csv', index=False)
                    print("Data saved to doctors_firecrawl.csv")
             else:
                print("Result structure:", result)
        except Exception as e:
            print(f"Error during fallback scraping: {e}")
            
    except Exception as e:
        print(f"Error during scraping: {e}")

if __name__ == "__main__":
    scrape_with_firecrawl()
