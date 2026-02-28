import requests
try:
    response = requests.head('https://www.marham.pk/doctors/lahore')
    print(response.status_code)
except Exception as e:
    print(e)
