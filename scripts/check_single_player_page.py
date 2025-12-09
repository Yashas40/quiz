import os, sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartquizarena.settings')
import django
django.setup()
from django.test import Client
from django.conf import settings

c = Client()
resp = c.get('/single-player/', SERVER_NAME='127.0.0.1')
print('STATUS', resp.status_code)
content = resp.content.decode('utf-8')
# check for csrf token input
has_csrf = 'name="csrfmiddlewaretoken"' in content
print('Has csrf token input:', has_csrf)
# check that JavaScript uses correct endpoints
uses_start = 'start-single-session' in content
uses_getnext = 'get-next-question' in content
print('start-single-session in page:', uses_start)
print('get-next-question in page:', uses_getnext)
# print a small snippet around csrf token
if has_csrf:
    idx = content.find('name="csrfmiddlewaretoken"')
    print('...snippet...')
    print(content[max(0, idx-80):idx+80])
