from django.test import Client
import json, random, time
from django.conf import settings

# Ensure test client host is allowed when running inside manage.py shell
if 'testserver' not in getattr(settings, 'ALLOWED_HOSTS', []):
    try:
        settings.ALLOWED_HOSTS = list(settings.ALLOWED_HOSTS) + ['testserver']
    except Exception:
        settings.ALLOWED_HOSTS = ['testserver']

c = Client()
# Start session
resp = c.post('/start-single-session/', data=json.dumps({'num_questions':5,'topics':[],'time_per_question_seconds':15}), content_type='application/json')
print('START STATUS', resp.status_code)
try:
    start_json = resp.json()
except Exception:
    print('Start response content:', resp.content)
    raise
print('START JSON', start_json)
sid = start_json.get('session_id')
print('SESSION ID', sid)
# Loop through questions
for qnum in range(1, 20):
    qresp = c.get(f'/get-next-question/{sid}/')
    qr = qresp.json()
    if qresp.status_code != 200 or 'error' in qr:
        print('GET NEXT QUESTION returned:', qresp.status_code, qr)
        break
    print(f"\nQUESTION {qnum}: {qr.get('question_text')}")
    opts = qr.get('options') or []
    for idx,opt in enumerate(opts):
        print(f"  {idx}: {opt}")
    # choose a random answer index as string
    if len(opts) == 0:
        chosen = ''
    else:
        chosen = str(random.randrange(len(opts)))
    post = c.post('/submit-answer/', data={'question_id': qr.get('id'), 'answer': chosen, 'session_id': sid})
    try:
        presp = post.json()
    except Exception:
        print('Submit content:', post.content)
        raise
    print('SUBMIT RESPONSE', presp)
    if presp.get('session_finished'):
        print('\nSession finished. Final summary:')
        print(presp.get('final_summary'))
        break
    # small pause
    time.sleep(0.1)
# After test, print DB PlayerScore
from quiz.models import PlayerScore, QuizSession
scores = PlayerScore.objects.filter(session_id=sid)
print('\nPlayerScore rows for session', sid, 'count=', scores.count())
for s in scores:
    print('Player:', getattr(s.player,'username',None), 'score', s.score, 'correct', s.correct_answers, 'total', s.total_answers)
