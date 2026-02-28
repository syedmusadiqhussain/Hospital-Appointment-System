from playwright.sync_api import sync_playwright
import pandas as pd
import re

def scrape_doctors():
    doctors_data = []
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )
        page = context.new_page()
        
        url = "https://www.marham.pk/doctors/lahore/cardiologist"
        print(f"Navigating to {url}...")
        page.goto(url)
        
        print("Waiting for content to load (3000ms)...")
        page.wait_for_timeout(3000)
        
        # Find all doctor cards
        # The structure is: <div class="row shadow-card">...</div>
        cards = page.locator('.row.shadow-card').all()
        print(f"Found {len(cards)} doctor cards.")
        
        for i, card in enumerate(cards):
            try:
                # Name
                name_el = card.locator('h3').first
                name = name_el.text_content().strip() if name_el.count() > 0 else "N/A"
                
                # Specialization
                # Structure: h3 -> parent a -> parent div -> parent div -> p (specialization)
                # Or just look for the p tag with class mb-0 mt-10 text-sm
                spec_el = card.locator('.col-9.col-md-10 > div > p.mb-0.mt-10.text-sm').first
                specialization = spec_el.text_content().strip() if spec_el.count() > 0 else "N/A"
                
                # Experience
                # Look for "Experience" text, then get the sibling p with class text-bold
                exp_container = card.locator('.col-4', has_text="Experience").first
                experience = "N/A"
                if exp_container.count() > 0:
                    exp_val = exp_container.locator('.text-bold').first
                    if exp_val.count() > 0:
                        experience = exp_val.text_content().strip()
                
                # Satisfaction
                sat_container = card.locator('.col-4', has_text="Satisfaction").first
                satisfaction = "N/A"
                if sat_container.count() > 0:
                    sat_val = sat_container.locator('.text-bold').first
                    if sat_val.count() > 0:
                        satisfaction = sat_val.text_content().strip()
                
                # Fee and Wait Time
                # These are in the "selectAppointmentOrOc" cards inside the main card
                # We'll take the first one found
                fee = "N/A"
                wait_time = "N/A"
                
                # Find the appointment/consultation cards
                appt_cards = card.locator('.selectAppointmentOrOc').all()
                if appt_cards:
                    # Prefer the first one
                    first_appt = appt_cards[0]
                    
                    # Fee
                    fee_el = first_appt.locator('.price').first
                    if fee_el.count() > 0:
                        fee_text = fee_el.text_content().strip()
                        # Extract numeric value
                        # "Rs. 2,500" -> 2500
                        fee_match = re.search(r'[\d,]+', fee_text)
                        if fee_match:
                            fee = fee_match.group().replace(',', '')
                    
                    # Wait Time / Availability
                    # "Available Today" is in a p tag with class text-wrap
                    wait_el = first_appt.locator('.text-wrap').first
                    if wait_el.count() > 0:
                        wait_time = wait_el.text_content().strip()
                
                # Clean up name (remove newlines if any)
                name = re.sub(r'\s+', ' ', name)
                
                doctor = {
                    "Name": name,
                    "Specialization": specialization,
                    "Experience": experience,
                    "Wait Time": wait_time,
                    "Consultation Fee": fee,
                    "Patient Satisfaction": satisfaction
                }
                doctors_data.append(doctor)
                # print(f"Scraped: {name}")
                
            except Exception as e:
                print(f"Error scraping card {i}: {e}")
        
        browser.close()
        
    # Save to CSV
    df = pd.DataFrame(doctors_data)
    df.to_csv('doctors_list.csv', index=False)
    print(f"Data saved to doctors_list.csv with {len(df)} records.")

if __name__ == "__main__":
    scrape_doctors()
