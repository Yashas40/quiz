import os, sys, asyncio
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartquizarena.settings')
import django
django.setup()

from channels.testing import WebsocketCommunicator
from quiz.consumers import QuizConsumer
import json

async def run_sim():
    app = QuizConsumer.as_asgi()
    # create two communicators
    c1 = WebsocketCommunicator(app, '/')
    c2 = WebsocketCommunicator(app, '/')

    connected1, _ = await c1.connect()
    connected2, _ = await c2.connect()
    print('connected1', connected1, 'connected2', connected2)

    # client1 creates room
    await c1.send_json_to({'action':'create', 'num_questions':3, 'topics':[], 'player':'alice'})
    msg = await c1.receive_json_from()
    print('c1 recv:', msg)
    # group broadcasts player_joined
    msg = await c1.receive_json_from()
    print('c1 recv:', msg)

    # get created room name
    room = msg['data'].get('players') and msg['data'].get('players')
    # but the create response had 'room' in first message
    created_msg = msg if msg.get('event')=='player_joined' else None
    # The first send_json_to created returned created event on c1's first receive earlier
    # Instead read the first message we got earlier (msg)

    # For robustness, read from c1 the 'created' event earlier
    # Reconnect to get created room from the earlier receive sequence
    # Let's inspect earlier prints

    # Now c2 joins: need room name from the 'created' response which should have been the first response from c1
    # For simplicity, fetch the created event by retrieving from c1's history: use c1.receive_json_from again until 'created'
    # But we've already consumed two messages. Instead, recreate flow: we'll start over by creating again but with clearer ordering.
    await c1.disconnect()
    await c2.disconnect()

async def run_clean():
    app = QuizConsumer.as_asgi()
    c1 = WebsocketCommunicator(app, '/')
    await c1.connect()
    await c1.send_json_to({'action':'create', 'num_questions':3, 'topics':[], 'player':'alice'})
    m1 = await c1.receive_json_from()  # created
    print('c1 m1:', m1)
    m2 = await c1.receive_json_from()  # player_joined (self)
    print('c1 m2:', m2)
    # support both old and new message shapes
    room = None
    if isinstance(m1, dict):
        room = (m1.get('data') or {}).get('room') or m1.get('room') or m1.get('room_name')

    c2 = WebsocketCommunicator(app, '/')
    await c2.connect()
    await c2.send_json_to({'action':'join', 'room': room, 'player':'bob'})
    # both clients should get player_joined
    print('c2 recv:')
    print(await c2.receive_json_from())
    print('c1 recv:')
    print(await c1.receive_json_from())

    # Now since two players present, server should send question events
    # c1 should receive a 'question'
    q1 = await c1.receive_json_from()
    print('c1 question:', q1)
    q2 = await c2.receive_json_from()
    print('c2 question:', q2)

    # Simulate both answering
    await c1.send_json_to({'action':'answer', 'room': room, 'player':'alice', 'selected':0})
    # c1 and c2 receive answer_result broadcast
    ar1 = await c1.receive_json_from()
    ar2 = await c2.receive_json_from()
    print('after alice answer -> c1:', ar1)
    print('after alice answer -> c2:', ar2)

    await c2.send_json_to({'action':'answer', 'room': room, 'player':'bob', 'selected':1})
    # both receive answer_result and possibly next question
    ar1b = await c1.receive_json_from()
    ar2b = await c2.receive_json_from()
    print('after bob answer -> c1:', ar1b)
    print('after bob answer -> c2:', ar2b)

    # collect until finished event
    # Since there are 3 questions, loop to consume remaining question/answer events until finished
    finished = False
    while not finished:
        ev = await c1.receive_json_from()
        print('c1 event:', ev)
        if ev.get('event') == 'finished':
            finished = True
            break
        # else if question, answer it
        if ev.get('event') == 'question':
            # send answers for both
            await c1.send_json_to({'action':'answer', 'room': room, 'player':'alice', 'selected':0})
            await c2.send_json_to({'action':'answer', 'room': room, 'player':'bob', 'selected':0})
            # consume broadcasts
            print('c1 got after answering:', await c1.receive_json_from())
            print('c2 got after answering:', await c2.receive_json_from())

    print('Simulation finished')
    await c1.disconnect()
    await c2.disconnect()

if __name__ == '__main__':
    asyncio.run(run_clean())
