from firecrawl import Firecrawl
import json

def debug_karachi():
    api_key = "fc-b06a2507bcd8448bbf8c64c69c178a98"
    app = Firecrawl(api_key=api_key)
    
    url = "https://www.marham.pk/doctors/karachi"
    print(f"Scraping {url} as markdown...")
    
    try:
        # Just get markdown to see if content is there
        if hasattr(app, 'v1') and app.v1:
            result = app.v1.scrape_url(url, formats=['markdown'], timeout=120000)
        else:
            result = app.scrape_url(url, formats=['markdown'], timeout=120000)
            
        if 'markdown' in result:
            md = result['markdown']
            print(f"Markdown length: {len(md)}")
            # Check for doctor names or listings
            if "Dr." in md:
                print("Found 'Dr.' in content.")
                # Print first 500 chars containing Dr.
                idx = md.find("Dr.")
                print(md[idx:idx+500])
            else:
                print("No 'Dr.' found in content.")
                print("First 1000 chars:")
                print(md[:1000])
        else:
            print("No markdown returned:", result)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_karachi()
