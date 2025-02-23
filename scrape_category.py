import requests
from bs4 import BeautifulSoup

session = requests.Session()
response = session.get('https://www.netsea.jp/login')
soup = BeautifulSoup(response.text, 'html.parser')
csrf_token = soup.find('input', {'name': '_token'})['value']
payload = {
    'login_id': 'doublenuts8',
    'password': 'Maropi888',
    '_token': csrf_token,
    'remember': 'on',
    'bookmark': 'on'
}
session.post('https://www.netsea.jp/login', data=payload)
category_response = session.get('https://www.netsea.jp/category/')
with open('/code/category_page.html', 'w', encoding='utf-8') as f:
    f.write(category_response.text)
print("HTML saved to /code/category_page.html")
