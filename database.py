import requests, os
from dotenv import load_dotenv
load_dotenv()

DB_URL = os.getenv('DB_URL')

def track_page(request, response):
    visitor_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    is_ssl = request.headers.get('X-Forwarded-Proto', 'http') == 'https'
    data = {
        'website_id': 'chat.overburn.dev',
        'page_url': request.path,
        'response_code': response.status_code,
        'visitor_id': visitor_ip,
        'referrer_url': request.referrer or '',
        'user_agent': request.user_agent.string,
        'method': request.method,
        'is_ssl': is_ssl
    }

    try:
        res = requests.post(DB_URL, json=data)
        if res.status_code not in range(200, 300):
            print(f'Error: pagehit_db API problem, Status Code: {res.status_code}')
    except requests.exceptions.RequestException as e:
        print('Error: pagehit_db API problem, unable to send page hit.')
