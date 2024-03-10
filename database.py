import requests

def track_page(request, response):
    url = 'http://127.0.0.1:8082/create'

    visitor_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    data = {
        'website_id': 'overburn.org',
        'page_url': request.path,
        'response_code': response.status_code,
        'visitor_id': visitor_ip,
        'referrer_url': request.referrer or '',
        'user_agent': request.user_agent.string,
        'method': request.method,
        'is_ssl': request.is_secure
    }

    try:
        res = requests.post(url, json=data)
        if res.status_code not in range(200, 300):
            print(f'Error: pagehit_db API problem, Status Code: {res.status_code}')
    except requests.exceptions.RequestException as e:
        print('Error: pagehit_db API problem, unable to send page hit.')
