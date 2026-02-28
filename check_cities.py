import requests
cities = ['lahore', 'karachi', 'islamabad', 'faisalabad', 'rawalpindi', 'multan', 'peshawar', 'quetta', 'gujranwala', 'sialkot']
for city in cities:
    try:
        url = f'https://www.marham.pk/doctors/{city}'
        response = requests.head(url)
        print(f"{city}: {response.status_code}")
    except Exception as e:
        print(f"{city}: {e}")
