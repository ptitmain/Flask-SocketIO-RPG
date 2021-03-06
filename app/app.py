#!/usr/bin/env python
from flask import Flask, render_template, session, request, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect
import json
from io import StringIO
import os.path

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
if os.path.isfile('data-save.json'):
    datafile = 'data-save.json'
else:
    datafile = 'data.json' 
with open(datafile) as dataf: 
    dataplayers = json.load(dataf)
dataf.close()

def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        socketio.sleep(10)
        count += 1
        #socketio.emit('my response', {'data': str(dataplayers)}, namespace='/test')
        socketio.emit('players', {'data': dataplayers}, namespace='/test')
        with open('data-save.json', 'w') as outfile:
            json.dump(dataplayers, outfile)


@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)

@app.route('/res/<path:path>')
def send_js(path):
    return send_from_directory('res', path)


@socketio.on('my event', namespace='/test')
def test_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': message['data'], 'count': session['receive_count']})

@socketio.on('createnpc', namespace='/test')
def test_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': 'GM: Creating NPC: ' + message['data'], 'count': session['receive_count']}, room='GM')
    dataplayers['players'].append({'name': message['data'], 'type': 'npc'})

    

@socketio.on('my broadcast event', namespace='/test')
def test_broadcast_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': message['data'], 'count': session['receive_count']},
         broadcast=True)


@socketio.on('join', namespace='/test')
def join(message):
    join_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})


@socketio.on('leave', namespace='/test')
def leave(message):
    leave_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})


@socketio.on('close room', namespace='/test')
def close(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response', {'data': 'Room ' + message['room'] + ' is closing.',
                         'count': session['receive_count']},
         room=message['room'])
    close_room(message['room'])


@socketio.on('my room event', namespace='/test')
def send_room_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': message['room'] + ': ' + message['data'], 'count': session['receive_count']},
         room=message['room'])


@socketio.on('disconnect request', namespace='/test')
def disconnect_request():
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': 'Disconnected!', 'count': session['receive_count']})
    disconnect()


@socketio.on('my ping', namespace='/test')
def ping_pong():
    emit('my pong')


@socketio.on('connect', namespace='/test')
def test_connect():
    global thread
    if thread is None:
        thread = socketio.start_background_task(target=background_thread)
    emit('my response', {'data': 'Connected', 'count': 0})


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected', request.sid)

@socketio.on('move', namespace='/test')
def move(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    newposition = json.load(StringIO(message['data']))
    #emit('my response', {'data': message['data'], 'count': 0}, broadcast=True)
    #f = open("log", "w")
    #f.write(str(newposition))
    #f.close()
    name = newposition['name']
    dataplayers['coord'][name] = {'x': newposition['x'], 'y': newposition['y'], 'zmap': newposition['zmap']}
      

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0')
